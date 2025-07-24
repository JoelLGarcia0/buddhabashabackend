from django.db import models
from cloudinary.models import CloudinaryField

class UserProfile(models.Model):
    clerk_user_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=50, blank=True) 
    last_name = models.CharField(max_length=50, blank=True)   
    shipping_address = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = CloudinaryField('image', folder='buddhabasha/')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=50, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.size or 'Default'}"
        
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image', folder='buddhabasha/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"
    
class Cart(models.Model):
    clerk_user_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    clerk_user_id = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    is_guest = models.BooleanField(default=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    # Stripe payment fields
    stripe_checkout_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_status = models.CharField(max_length=100, null=True, blank=True)

   # for shipping integration
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    shipping_address = models.JSONField(null=True, blank=True)  # you can use a JSONField if needed
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_label_url = models.URLField(max_length=1000,null=True, blank=True)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    shipping_provider = models.CharField(max_length=100, null=True, blank=True)
    shipping_service = models.CharField(max_length=200, null=True, blank=True)
    is_shipped = models.BooleanField(default=False)
    shipped_at = models.DateTimeField(null=True, blank=True)
    shippo_shipment_id = models.CharField(max_length=255, null=True, blank=True)


    # For custom parcel input 
    parcel_length = models.DecimalField(max_digits=5, decimal_places=2, default=6.00)
    parcel_width = models.DecimalField(max_digits=5, decimal_places=2, default=4.00)
    parcel_height = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    parcel_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)  # in pounds
    selected_rate_id = models.CharField(max_length=255, null=True, blank=True) 
  

    def grand_total(self):
        return self.subtotal + self.shipping_cost

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)