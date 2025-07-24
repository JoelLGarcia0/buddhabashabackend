from shippo import Shippo
from shippo.models import components
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from store.models import Order
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import HttpResponse
import json
from store.utils import fetch_rates_for_order


def preview_rates_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if request.method == "POST":
        order.parcel_length = request.POST.get("parcel_length") or order.parcel_length
        order.parcel_width = request.POST.get("parcel_width") or order.parcel_width
        order.parcel_height = request.POST.get("parcel_height") or order.parcel_height
        order.parcel_weight = request.POST.get("parcel_weight") or order.parcel_weight
        order.save()

    rates, shipment_id = fetch_rates_for_order(
        order,
        order.parcel_length,
        order.parcel_width,
        order.parcel_height,
        order.parcel_weight,
    )

    order.shippo_shipment_id = shipment_id
    order.save()

    return render(request, "admin/preview_rates.html", {
        "order": order,
        "rates": sorted(rates, key=lambda r: float(r.amount)),
        "refreshed": True 
    })


@csrf_exempt
def generate_label_view(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, pk=order_id)

        # Save parcel size and rate from form
        order.parcel_length = request.POST.get("parcel_length") or order.parcel_length
        order.parcel_width = request.POST.get("parcel_width") or order.parcel_width
        order.parcel_height = request.POST.get("parcel_height") or order.parcel_height
        order.parcel_weight = request.POST.get("parcel_weight") or order.parcel_weight
        order.selected_rate_id = request.POST.get("selected_rate_id")
        order.save()

        if not order.shippo_shipment_id or not order.selected_rate_id:
            messages.error(request, "❌ Missing shipment or rate ID.")
            return redirect(f"/admin/store/order/{order.id}/change/")

        shippo_sdk = Shippo(api_key_header=settings.SHIPPO_API_KEY)

        try:
            shipment = shippo_sdk.shipments.get(order.shippo_shipment_id)

            rate = next((r for r in shipment.rates if r.object_id == order.selected_rate_id), None)
            if not rate:
                messages.error(request, "❌ Selected rate not found.")
                return redirect(f"/admin/store/order/{order.id}/change/")

            transaction = shippo_sdk.transactions.create(
                components.TransactionCreateRequest(
                    rate=rate.object_id,
                    label_file_type=components.LabelFileTypeEnum.PDF,
                    async_=False
                )
            )

            if transaction.status != "SUCCESS":
                error_msg = ", ".join([msg.text for msg in transaction.messages])
                messages.error(request, f"❌ Shippo error: {error_msg}")
                return redirect(f"/admin/store/order/{order.id}/change/")

            # Save shipping details
            order.shipping_label_url = transaction.label_url
            order.tracking_number = transaction.tracking_number
            order.shipping_provider = rate.provider
            order.shipping_service = getattr(rate.servicelevel, "name", "")
            order.is_shipped = True
            order.shipped_at = timezone.now()
            order.save()

            # Email the customer
            html_message = render_to_string("emails/shipping_confirmation.html", {
                "order": order,
                "tracking_number": transaction.tracking_number,
                "tracking_url": transaction.tracking_url_provider,
                "shipping_label_url": transaction.label_url,
            })

            email = EmailMessage(
                subject="Your BuddhaBasha Order Has Shipped!",
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.email],
            )
            email.content_subtype = "html"
            email.send()

            messages.success(request, "✅ Shipping label created and email sent!")

        except Exception as e:
            messages.error(request, f"❌ Unexpected error: {str(e)}")

        return redirect(f"/admin/store/order/{order.id}/change/")
    