from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from store.models import Order, ProductVariant, Product
from store.serializers import OrderSerializer
import json
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(clerk_user_id=self.request.clerk_user_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeCheckoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        line_items = []
        subtotal = 0
        out_of_stock_items = []

        clerk_user_id = request.data.get('clerk_user_id', "")
        is_guest = clerk_user_id.startswith("guest_")

        for item in data['items']:
            try:
                variant = ProductVariant.objects.select_related('product').get(id=item['variant'])
                quantity = int(item['quantity'])
                product = variant.product
                price = float(product.price)

                if variant.stock < quantity:
                    out_of_stock_items.append({
                        "product": product.name,
                        "variant": variant.size,
                        "requested": quantity,
                        "available": variant.stock
                    })
                    continue

                subtotal += quantity * price

                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(price * 100),
                        'product_data': {
                            'name': f"{product.name} - {variant.size or 'Default'}",
                            'description': product.description,
                            'images': [request.build_absolute_uri(product.image.url)] if product.image else [],
                        },
                    },
                    'quantity': quantity,
                })
                
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=400)

        if out_of_stock_items:
            return Response({
                "error": "items are out of stock",
                "details": out_of_stock_items
            }, status=400)

        # Create Stripe Checkout Session with all needed metadata
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=data.get('email', ''),
            line_items=line_items,
            mode='payment',
            shipping_options=[
        {
            'shipping_rate_data': {
                'type': 'fixed_amount',
                'fixed_amount': {'amount': 500, 'currency': 'usd'},
                'display_name': 'Standard Shipping',
                'delivery_estimate': {
                    'minimum': {'unit': 'business_day', 'value': 3},
                    'maximum': {'unit': 'business_day', 'value': 5},
                },
            }
        }
    ],
            success_url='https://www.buddhabashajewelry.com/success',
            cancel_url='https://www.buddhabashajewelry.com/cancel',
            metadata={
                'email': data.get('email', ''),
                'clerk_user_id': str(clerk_user_id or ''),
                'is_guest': str(is_guest),
                'shipping_address': json.dumps(data.get('shipping_address', {})),
                'shipping_cost': "5.00",
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
            },
            client_reference_id=str(clerk_user_id or 'guest')
        )

        return Response({'checkout_url': session.url})
   