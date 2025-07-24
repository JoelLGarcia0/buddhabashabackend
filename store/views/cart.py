from rest_framework import viewsets, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from store.models import Cart, CartItem
from store.serializers import CartSerializer, CartItemSerializer, CartItemCreateSerializer


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]  # Temporarily allow any access for testing

    def get_queryset(self):
        user_id = self.request.query_params.get('clerk_user_id')
        if user_id:
            return Cart.objects.filter(clerk_user_id=user_id)
        return Cart.objects.none()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]  # Temporarily allow any access for testing

    def get_queryset(self):
        user_id = (
            self.request.query_params.get('clerk_user_id')
            or getattr(self.request, 'clerk_user_id', None)
    )

        if not user_id:
            session_key = self.request.session.session_key or self.request.session.save() or self.request.session.session_key
            user_id = f"guest_{session_key}"

        return CartItem.objects.filter(cart__clerk_user_id=user_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return CartItemCreateSerializer
        return CartItemSerializer

    def perform_create(self, serializer):
        user_id = (
            self.request.data.get("clerk_user_id")
            or getattr(self.request, "clerk_user_id", None)
    )

        if not user_id:
            session_key = self.request.session.session_key or self.request.session.save() or self.request.session.session_key
            user_id = f"guest_{session_key}"

        user_cart, _ = Cart.objects.get_or_create(clerk_user_id=user_id)

    # Now safe to access validated data
        variant = serializer.validated_data['variant']
        quantity = serializer.validated_data['quantity']

    # Check for existing cart item
        existing_item = CartItem.objects.filter(cart=user_cart, variant=variant).first()
        if existing_item:
            new_total_quantity = existing_item.quantity + quantity
            if new_total_quantity > variant.stock:
                raise serializers.ValidationError("Cannot add more than available stock.")
            existing_item.quantity = new_total_quantity
            existing_item.save()
            return

        if quantity > variant.stock:
            raise serializers.ValidationError("Not enough stock available.")

        serializer.save(cart=user_cart)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        obj = queryset.filter(pk=lookup_value).first()
        if not obj:
            raise NotFound("No CartItem matches the given query.")
        return obj

    def perform_update(self, serializer):
        item = self.get_object()
        quantity = serializer.validated_data.get('quantity')
        if quantity > item.variant.stock:
            raise serializers.ValidationError("Not enough stock available.")
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

class CleanCartStockView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        clerk_user_id = request.data.get("clerk_user_id")
        is_guest = request.data.get("is_guest")
        if is_guest is None:
            is_guest = not bool(clerk_user_id) or str(clerk_user_id).startswith("guest_")


        try:
            cart = Cart.objects.get(clerk_user_id=clerk_user_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=404)

        updated_items = []
        removed_items = []

        for item in cart.items.all():
            variant = item.variant
            product = variant.product
            if variant.stock == 0:
                removed_items.append({
                    "product": product.name,
                    "reason": "out_of_stock"
                })
                item.delete()
            elif item.quantity > variant.stock:
                item.quantity = variant.stock
                item.save()
                updated_items.append({
                    "product": product.name,
                    "adjusted_to": variant.stock,
                    "reason": "reduced_to_match_stock"
                })

        return Response({
            "removed": removed_items,
            "adjusted": updated_items,
            "message": "Cart cleaned successfully"
        })
 