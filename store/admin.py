from django.contrib import admin
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.html import format_html
from django.conf import settings
import requests

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem,
    ProductImage, ProductVariant, UserProfile
)

# ---------- Global Admin Config ----------
admin.site.site_header = "BuddhaBasha Admin"
admin.site.site_title = "BuddhaBasha Admin Portal"
admin.site.index_title = "Welcome to BuddhaBasha Admin"

# ---------- Inline Admins ----------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "price", "quantity")

# ---------- Product Admin ----------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductVariantInline]
    list_display = ["name"]
    list_filter = ("category",)

# ---------- Category Admin ----------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

# ---------- Cart Admin ----------
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("clerk_user_id", "created_at")
    search_fields = ("clerk_user_id",)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("variant", "cart", "quantity")
    list_filter = ("variant",)

# ---------- UserProfile Admin ----------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("clerk_user_id", "email", "first_name", "last_name")
    search_fields = ("clerk_user_id", "email", "first_name", "last_name")
    list_filter = ("updated_at",)

# ---------- Order Admin ----------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

    list_display = [
        "id", "email", "is_shipped", 
        "shipping_provider", "shipping_service", 
        "grand_total_display", "preview_rates_button"
    ]

    fields = [
        "email", "is_guest", "subtotal", "grand_total_display",
        "first_name", "last_name", "shipping_address",
        "parcel_length", "parcel_width", "parcel_height", "parcel_weight",
        "selected_rate_id",
        "shipping_label_url", "tracking_number",
        "shipping_provider", "shipping_service", "is_shipped", "shipped_at","shippo_shipment_id" 
    ]

    readonly_fields = [
        "grand_total_display", "shipping_label_url", "tracking_number", 
        "shipping_provider", "shipping_service", "shipped_at", "preview_rates_button","shippo_shipment_id"
    ]
 
    
    def preview_rates_button(self, obj):
        url = reverse("preview_rates", args=[obj.id])
        return format_html('<a class="button" href="{}">🚚 Shipping Details</a>', url)


    def grand_total_display(self, obj):
        return f"${obj.grand_total():.2f}"
    grand_total_display.short_description = "Total"