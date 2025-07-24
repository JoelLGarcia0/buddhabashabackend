import json
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from store.models import Order, OrderItem, ProductVariant, Cart, Product

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f"⚠️ Webhook error: {e}")
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")
        payment_status = session.get("payment_status")
        email = session.get("customer_email")
        metadata = session.get("metadata", {})

        shipping_address = json.loads(metadata.get("shipping_address", "{}"))
        shipping_cost = float(metadata.get("shipping_cost", "0.00"))
        clerk_user_id = metadata.get("clerk_user_id", "")
        is_guest = metadata.get("is_guest").lower() == "true"

        try:
            # Reconstruct total & items
            line_items = stripe.checkout.Session.list_line_items(session_id)
            subtotal = sum(item.amount_total for item in line_items.data) / 100

            first_name = metadata.get("first_name", "").strip()
            last_name = metadata.get("last_name", "").strip()

            # Create Order
            order = Order.objects.create(
                clerk_user_id=clerk_user_id or None,
                email=email,
                is_guest=is_guest,
                subtotal=subtotal,
                stripe_checkout_id=session_id,
                stripe_payment_status=payment_status,
                shipping_address=shipping_address,
                shipping_cost=shipping_cost,
                first_name=first_name,
                last_name=last_name,
            )

            # Add OrderItems
            for item in line_items.data:
                product_name = item.description
                quantity = item.quantity
                unit_price = item.amount_total / quantity / 100

                variant = ProductVariant.objects.select_related("product").filter(
                    product__name__in=product_name.split(" - "),
                    size=product_name.split(" - ")[-1] if " - " in product_name else None
                ).first()

                if variant:
                    OrderItem.objects.create(
                        order=order,
                        variant=variant,
                        quantity=quantity,
                        price=unit_price,
    )
                    variant.stock = max(variant.stock - quantity, 0)
                    variant.save()
                else:
                    print(f"⚠️ Variant not found for name: {product_name}")

            # Clear cart if user is logged in
            if clerk_user_id:
                cart = Cart.objects.filter(clerk_user_id=clerk_user_id).first()
                if cart:
                    cart.delete()
                    print(f"🧹 Cart cleared for user: {clerk_user_id}")

            # Send confirmation email
            if order.email:
                saved_items = order.items.select_related("variant__product")


                html_message = render_to_string("emails/order_confirmation.html", {
                    "first_name": order.first_name,
                    "order_id": order.id,
                    "items": saved_items,
                    "total": order.grand_total,
                    "shipping_cost": order.shipping_cost,
                    "shipping_address": order.shipping_address,
                    "now": timezone.now(),

                })

                email_msg = EmailMessage(
                    subject=f"Your BuddhaBasha Order #{order.id}",
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[order.email],
                )
                email_msg.content_subtype = "html"
                email_msg.send(fail_silently=False)
                print("📧 Confirmation email sent")

                try:
                    owner_email = settings.STORE_OWNER_EMAIL  # Replace with actual email or pull from settings

                    internal_html = render_to_string("emails/order_notification.html", {
                        "first_name": order.first_name,
                        "last_name": order.last_name,
                        "order_id": order.id,
                        "items": saved_items,
                        "total": order.grand_total,
                        "shipping_cost": order.shipping_cost,
                        "shipping_address": order.shipping_address,
                        "customer_email": order.email,
                        "now": timezone.now(),
    })

                    owner_msg = EmailMessage(
                        subject=f"🛍️ New Order #{order.id} - BuddhaBasha",
                        body=internal_html,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[owner_email],
    )
                    owner_msg.content_subtype = "html"
                    owner_msg.send(fail_silently=False)
                    print("📧 Notification email sent to store owner")
                except Exception as e:
                    print(f"❌ Failed to send store owner email: {e}")

        except Exception as e:
            print(f"❌ Failed to process webhook: {e}")

    return HttpResponse(status=200)

   

@csrf_exempt
def clerk_user_created_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    data = json.loads(request.body)
    print("✅ Clerk Webhook received:", data)

    email = data.get("data", {}).get("email_addresses", [{}])[0].get("email_address")
    clerk_user_id = data.get("data", {}).get("id")


    if email and clerk_user_id:
        from store.models import Order
        updated = Order.objects.filter(
            email=email,
            clerk_user_id__startswith="guest_"
        ).update(
            clerk_user_id=clerk_user_id,
            is_guest=False
        )
        print(f"🔄 Updated {updated} guest order(s) for user {clerk_user_id}")

    return JsonResponse({"status": "success"}, status=200)
