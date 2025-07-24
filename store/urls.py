from django.urls import path, include
from rest_framework.routers import DefaultRouter
from store.views.products import ProductViewSet, CategoryViewSet
from store.views.cart import CartViewSet, CartItemViewSet, CleanCartStockView
from store.views.orders import OrderViewSet, StripeCheckoutView
from store.views.webhooks import stripe_webhook, clerk_user_created_webhook
from store.views.users import UserProfileView
from store.views.shipping import preview_rates_view, generate_label_view



# Create router and register viewsets
router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'cart-items', CartItemViewSet, basename='cart-items')

urlpatterns = [
    path('', include(router.urls)),
    path('create-checkout-session/', StripeCheckoutView.as_view(), name = 'stripe_checkout'),
    path('stripe-webhook/', stripe_webhook),
    path("clean-cart-stock/", CleanCartStockView.as_view(), name="clean_cart_stock"),
    path("clerk-user-created/", clerk_user_created_webhook,),
    path("user-profile/<str:clerk_user_id>/", UserProfileView.as_view(), name="user_profile_get"),
    path("user-profile/", UserProfileView.as_view(), name="user_profile_post"),
    path("admin/order/<int:order_id>/rates/", preview_rates_view, name="preview_rates"),
    path("admin/order/<int:order_id>/generate-label/", generate_label_view, name="generate_label"),

]