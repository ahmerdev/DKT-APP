from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.utils import timezone
from django.db import models
import random
from django.contrib.auth.hashers import make_password
from datetime import timedelta


class Category(models.Model):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='category/images/', blank=True, null=True)
    bg_color = models.CharField(max_length=7, default="#FFFFFF")
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to="brands/images/", blank=True, null=True)
    bg_color = models.CharField(max_length=7, default="#FFFFFF")
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Banner(models.Model):   
    category = models.ManyToManyField(Category, related_name="banners", blank=True)
    brand = models.ManyToManyField(Brand, related_name="banners", blank=True)
    image = models.ImageField(upload_to="banners/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banner - {self.category.name}"
    

class Ad(models.Model):   
    category = models.ManyToManyField(Category, related_name="ads", blank=True)
    brand = models.ManyToManyField(Brand, related_name="ads", blank=True)
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

class Privacy(models.Model):   
    p_title = models.CharField(max_length=200)
    t_title = models.CharField(max_length=200)
    p_text = models.TextField(blank=True, null=True)
    t_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.p_title    
    
class About(models.Model):   
    title = models.CharField(max_length=200)
    text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title      

class ContactInfo(models.Model):
    title = models.CharField(max_length=200, default="Contact Us")
    tagline = models.CharField(max_length=250, blank=True, null=True)  # Happy to Help etc.
    
    mailing_address = models.TextField()
    helpline_number = models.CharField(max_length=100)
    corporate_contact = models.CharField(max_length=100, blank=True, null=True)

    email_generic = models.EmailField(max_length=200, blank=True, null=True)
    email_collaboration = models.EmailField(max_length=200, blank=True, null=True)
    email_hr = models.EmailField(max_length=200, blank=True, null=True)

    drop_us_line_text = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
   

class ContactForm(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=100)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"




class Product(models.Model):
    STOCK_CHOICES = [
        ('instock', 'In Stock'),
        ('outofstock', 'Out of Stock'),
    ]

    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple'),
        ('variable', 'Variable'),
    ]
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

    offer = models.CharField(max_length=255, blank=True, null=True)

    short_description = models.TextField(max_length=300)
    description = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to="products/main/", null=True, blank=True)  
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    sku = models.CharField(max_length=100, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0, null=True, blank=True)

    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES, default="instock")
    points = models.PositiveIntegerField(default=0, null=True, blank=True)

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default="simple")
    position = models.PositiveIntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return f"Image for {self.product.name}"
    
    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


# Variant Options (e.g. Color, Size)
class VariantOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variant_options")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ['product', 'name']  

    def __str__(self):
        return f"{self.name} - {self.product.name}"


# Variant Values (e.g. Red, Blue, Small, Large)
class VariantValue(models.Model):
    option = models.ForeignKey(VariantOption, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = ['option', 'value']  

    def __str__(self):
        return f"{self.value} ({self.option.name})"


# Variant Combination
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=100, null=True, blank=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(default=dict)
    image = models.ImageField(upload_to="products/variants/", null=True, blank=True)
    is_active = models.BooleanField(default=True)  

    class Meta:
        unique_together = ['product', 'attributes']  

    def __str__(self):
        return f"Variant {self.sku or self.id} - {self.product.name}"


# User Login System 

# class CustomUser(AbstractUser):
#     username = None  # username field hata diya
#     phone_number = models.CharField(max_length=20, unique=True)
#     is_phone_verified = models.BooleanField(default=False)

#     USERNAME_FIELD = "phone_number"
#     REQUIRED_FIELDS = []  # koi extra field compulsory nahi

#     def __str__(self):
#         return self.phone_number

class PointSetting(models.Model):
    registration_bonus_points = models.IntegerField(default=20, help_text="Points given on new registration")
    point_value = models.DecimalField(max_digits=5, decimal_places=2, default=0.50, help_text="Currency value of 1 point (e.g., 0.5 means 1 point = Rs 0.50)")

    class Meta:
        verbose_name = "Point Configuration"
        verbose_name_plural = "Point Configuration"

    def save(self, *args, **kwargs):
        if not self.pk and PointSetting.objects.exists():
            raise ValueError("Only one Point Configuration instance is allowed.")
        return super().save(*args, **kwargs)

class AppUser(models.Model):
    number = models.CharField(max_length=20, unique=True)   
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=254,unique=True, null=True, blank=True, validators=[validate_email], db_index=True)   
    image = models.ImageField(upload_to="users/", blank=True, null=True)  
    points = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    password_hash = models.CharField(max_length=255)  
    api_token = models.CharField(max_length=128, blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)      
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.number

     # OTP generator
    def generate_otp(self):

        otp = str(random.randint(100000, 999999))

        self.otp = otp

        self.otp_created_at = timezone.now()

        self.save()

        return otp


    # OTP expiry check
    def is_otp_expired(self):

        if not self.otp_created_at:
            return True

        return timezone.now() > self.otp_created_at + timedelta(minutes=5)


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
    city = models.ForeignKey("City", on_delete=models.SET_NULL, null=True, blank=True)
    rider = models.ForeignKey("Rider", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending") 
    cancel_reason = models.TextField(blank=True, null=True)
    points_used = models.IntegerField(default=0)
    points_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_points_added = models.BooleanField(default=False)
    discount_code = models.CharField(max_length=50, null=True, blank=True)
    discount_type = models.CharField(max_length=20, default="", blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="order_items/", null=True, blank=True)
    name = models.CharField(max_length=255)
    pts = models.IntegerField()
    variants = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.product and self.cost_price is None:
            self.cost_price = self.product.cost_price
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
    max_uses = models.PositiveIntegerField(null=True, blank=True)  
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
    

class Review(models.Model):
    item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='user_reviews', null=True, blank=True)
    rating = models.IntegerField()  
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.number} — {self.product.title}"
    
class Rider(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    designation = models.CharField(max_length=100, default="Delivery Rider")
    is_active = models.BooleanField(default=True)
    cities = models.ManyToManyField("City", related_name="riders")

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # auto hash only if not hashed
        if not self.password.startswith("pbkdf2"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
class City(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name   


import uuid
class RiderPasswordResetToken(models.Model):
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # 1 ghante tak valid rahega
        return not self.is_used and (timezone.now() - self.created_at).seconds < 3600

    def __str__(self):
        return f"Reset token for {self.rider.name}"    
    

class UsedCoupon(models.Model):
    user = models.ForeignKey("AppUser", on_delete=models.CASCADE, related_name='used_coupons')
    discount = models.ForeignKey("Discount", on_delete=models.CASCADE, related_name='coupon_uses')
    order = models.ForeignKey("Order", on_delete=models.SET_NULL, null=True, blank=True, related_name='used_discounts')
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'discount') 
    def __str__(self):
        return f"{self.user.name if self.user.name else self.user.number} used {self.discount.code}"    


class DiscountPopup(models.Model):
        is_active = models.BooleanField(default=True)

        banner = models.ImageField(upload_to="discount/banner/", blank=True, null=True)
        products = models.ForeignKey('Product',on_delete=models.SET_NULL, blank=True, null=True)
        brand = models.ForeignKey('Brand', on_delete=models.SET_NULL, blank=True, null=True)
        category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)

        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"Discount Popup #{self.id}"
