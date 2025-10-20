from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.utils import timezone
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='category/images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to="brands/images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Banner(models.Model):   
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="banners")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="banners")
    image = models.ImageField(upload_to="banners/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banner - {self.category.name}"
    

class Ad(models.Model):   
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="ads")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="ads")
    image = models.ImageField(upload_to="ads/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ad - {self.category.name}"
    

class Hero(models.Model):   
    title = models.CharField(max_length=200)
    subtext = models.CharField(max_length=200)
    image = models.ImageField(upload_to="heros/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Product(models.Model):
    STOCK_CHOICES = [
        ('instock', 'In Stock'),
        ('outofstock', 'Out of Stock'),
    ]

    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple'),
        ('variable', 'Variable'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

    short_description = models.TextField(max_length=300)
    description = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to="products/main/", null=True, blank=True)  
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    SKU = models.CharField(max_length=100, unique=True, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0, null=True, blank=True)

    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES, default="instock")
    points = models.PositiveIntegerField(default=0, null=True, blank=True)

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default="simple")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return f"Image for {self.product.name}"


# Variant Options (e.g. Color, Size)
class VariantOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variant_options")
    name = models.CharField(max_length=100)  

    def __str__(self):
        return f"{self.name} - {self.product.name}"


# Variant Values (e.g. Red, Blue, Small, Large)
class VariantValue(models.Model):
    option = models.ForeignKey(VariantOption, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=100)  # Example: "Red", "Large"

    def __str__(self):
        return f"{self.value} ({self.option.name})"


# Variant Combination (e.g. Size: Large + Color: Red → SKU/Price/Stock)
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(default=dict)
    image = models.ImageField(upload_to="products/variants/", null=True, blank=True)

    def __str__(self):
        return f"Variant {self.sku} - {self.product.name}"


# User Login System 

# class CustomUser(AbstractUser):
#     username = None  # username field hata diya
#     phone_number = models.CharField(max_length=20, unique=True)
#     is_phone_verified = models.BooleanField(default=False)

#     USERNAME_FIELD = "phone_number"
#     REQUIRED_FIELDS = []  # koi extra field compulsory nahi

#     def __str__(self):
#         return self.phone_number

class AppUser(models.Model):
    number = models.CharField(max_length=20, unique=True)   
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=254,unique=True, null=True, blank=True, validators=[validate_email], db_index=True)   
    image = models.ImageField(upload_to="users/", blank=True, null=True)  
    password_hash = models.CharField(max_length=255)  
    api_token = models.CharField(max_length=128, blank=True, null=True)      
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.number

class Address(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}, {self.country}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("process", "In Process"),
        ("cancelled", "Cancelled"),
        ("delivered", "Delivered"),
        ("on_the_way", "On The Way"),
    ]
    TYPE_CHOICES = [
       ("normal", "Normal Order"),
        ("redeem", "Redeem Order"),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="normal")
    user = models.ForeignKey(  
        "AppUser", 
        related_name="orders", 
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    address = models.TextField()
    shipping = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending") 
    created_at = models.DateTimeField(auto_now_add=True)

    def update_order_type(self):
                items = self.items.all()
                if items.exists() and all(item.price == 0 for item in items):
                    self.type = "redeem"
                else:
                    self.type = "normal"
                self.save()

    def __str__(self):
                return f"Order #{self.id} - {self.get_type_display()}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="order_items/", null=True, blank=True)
    name = models.CharField(max_length=255)
    pts = models.IntegerField()
    variants = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.update_order_type()

class Payment(models.Model):
    order = models.ForeignKey(Order, related_name="payments", on_delete=models.CASCADE)
    method = models.CharField(max_length=100)
    status = models.CharField(max_length=50)


class Redeem(models.Model):
    subtitle = models.CharField(max_length=255)
    title = models.CharField(max_length=255)  
    description = models.TextField() 
    points_required = models.PositiveIntegerField(default=0)  # e.g. 460
    image = models.ImageField(upload_to="redeem/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.points_required} PTS)"    
    


class Discount(models.Model):
    PERCENTAGE = 'percentage'
    FIXED = 'fixed'

    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, 'Percentage'),
        (FIXED, 'Fixed Amount'),
    ]
    title = models.CharField(max_length=50)
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    products = models.ManyToManyField(Product, blank=True)
    users = models.ManyToManyField(AppUser, blank=True)
    apply_all_products = models.BooleanField(default=False)
    apply_all_users = models.BooleanField(default=False)
    max_uses = models.PositiveIntegerField(null=True, blank=True)  # Overall max uses
    used_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid_for_user(self, user):
        from django.utils import timezone
        now = timezone.now()
        if not self.active or not (self.start_date <= now <= self.end_date):
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        if self.users.exists() and user not in self.users.all():
            return False
        return True