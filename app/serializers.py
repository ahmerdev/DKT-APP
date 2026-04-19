from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db.models import Sum, Avg, Q
import ast
from .sms import send_sms
from .models import Category, Brand, PointSetting, Product, Discount, Redeem, Banner, Hero, Ad, ProductImage, ProductVariant, Order, OrderItem, Payment, AppUser, Privacy, Review, About, ContactInfo, ContactForm, Address

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'is_active', 'image', 'created_at']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'is_active', 'image', 'created_at']      

class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Privacy
        fields = ['id', 'p_title', 't_title', 'p_text', 't_text', 'created_at']      

class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = ['id', 'title', 'text', 'created_at']     

class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['id', 'title', 'tagline', 'mailing_address', 'helpline_number', 'corporate_contact', 'email_generic', 'email_collaboration', 'email_hr', 'drop_us_line_text', 'created_at']     

class ContactFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactForm
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'message', 'created_at']             

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'item', 'user', 'rating', 'comment', 'created_at']

class BannerSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()   
    brand = serializers.StringRelatedField() 
    class Meta:
        model = Banner
        fields = ["id", "category", "brand", "image", "created_at"]   


class AdSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()   
    brand = serializers.StringRelatedField() 
    class Meta:
        model = Ad
        fields = ["id", "category", "brand", "image", "created_at"] 


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hero
        fields = ['id', 'title', 'subtext', 'image', 'created_at']          



class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "price", "stock", "attributes", "is_active", "image"]



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class RedeemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redeem
        fields = [
            "id",
            "subtitle",
            "title",
            "description",
            "points_required",
            "image",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    brand = serializers.StringRelatedField()
    gallery_images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    reviews = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "image",
            "cost_price",
            "regular_price",
            "sale_price",
            "sku",
            "quantity",
            "is_active",
            "stock_status",
            "points",
            "product_type",
            "category",
            "brand",
            "gallery_images",
            "variants",
            "reviews",
            "avg_rating",
            "total_reviews",
            "created_at",
            "updated_at",
        ]

    def get_reviews(self, obj):
        order_items = OrderItem.objects.filter(
            Q(product=obj) | Q(name=obj.name)
        )
        reviews_qs = Review.objects.filter(item__in=order_items).order_by('-created_at')
        return ReviewSerializer(reviews_qs, many=True).data

    def get_avg_rating(self, obj):
        order_items = OrderItem.objects.filter(
            Q(product=obj) | Q(name=obj.name)
        )
        reviews_qs = Review.objects.filter(item__in=order_items)
        if reviews_qs.exists():
            return round(reviews_qs.aggregate(avg=Avg('rating'))['avg'], 2)
        return 0

    def get_total_reviews(self, obj):
        order_items = OrderItem.objects.filter(
            Q(product=obj) | Q(name=obj.name)
        )
        return Review.objects.filter(item__in=order_items).count()






class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [ "id",'image', 'name', 'pts', 'variants', 'price', 'quantity', 'cost_price']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['method', 'status']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'state', 'postal_code', 'country']

class AppUserRegisterStepOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ["number"]

    def validate_number(self, value):
        import re
        if not re.fullmatch(r"\+?\d{9,15}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

class AppUserRegisterStepTwoSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=True)

    class Meta:
        model = AppUser
        fields = ["name", "email", "password"]  

    def update(self, instance, validated_data):
        from django.contrib.auth.hashers import make_password
        instance.name = validated_data.get("name", instance.name)
        instance.email = validated_data.get("email", instance.email)
        if "password" in validated_data:
            instance.password_hash = make_password(validated_data["password"])
        instance.save()
        return instance


class AppUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_hash = serializers.CharField(read_only=True)
    addresses = AddressSerializer(many=True, required=False)

    # NAYE DYNAMIC FIELDS (YEH ADD KARNA HAI API RESPONSE MEIN)
    point_value = serializers.SerializerMethodField(read_only=True)
    points_in_rupees = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AppUser
        fields = [
            "id", "number", "name", "email", "image", "is_active", 
            "password", "password_hash", "created_at", "api_token", "addresses",
            "points", "point_value", "points_in_rupees"  
        ]
        read_only_fields = ["id", "created_at", "password_hash", "api_token", "points", "point_value", "points_in_rupees"]

    def validate_number(self, value):
        import re
        if not re.fullmatch(r"\+?\d{9,15}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        addresses_data = validated_data.pop("addresses", None)
        password = validated_data.pop("password")
        validated_data["password_hash"] = make_password(password)
        user = super().create(validated_data)
        if addresses_data:
            for addr_data in addresses_data:
                Address.objects.create(user=user, **addr_data)
        return user

    def update(self, instance, validated_data):
        from django.contrib.auth.hashers import make_password
        instance.name = validated_data.get("name", instance.name)
        instance.email = validated_data.get("email", instance.email)
        instance.image = validated_data.get("image", instance.image)
        instance.save()
        return instance
    
    def get_point_value(self, obj):
        from .models import PointSetting
        setting = PointSetting.objects.first()
        return float(setting.point_value) if setting else 0.50

    def get_points_in_rupees(self, obj):
        setting = PointSetting.objects.first()
        point_val = float(setting.point_value) if setting else 0.50
        return round((obj.points or 0) * point_val, 2)

    # Method to calculate total points
    # def get_total_points(self, obj):
    #     normal_pts = (
    #         Order.objects.filter(user=obj, type="normal", status="delivered")
    #         .aggregate(total=Sum("items__pts"))["total"]
    #         or 0
    #     )
    #     redeem_pts = (
    #         Order.objects.filter(user=obj, type="redeem", status="delivered")
    #         .aggregate(total=Sum("items__pts"))["total"]
    #         or 0
    #     )
    #     return normal_pts - redeem_pts


# class SimpleUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AppUser
#         fields = ['id', 'number', 'name', 'email'] 

class OrderSerializer(serializers.ModelSerializer):
    user_detail = AppUserSerializer(source="user", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    address = serializers.SerializerMethodField()
    shipping = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [ 'id', 'user_detail', 'address', 'shipping', 'status', 'type', 'items', 'payments',"points_used",       
            "points_discount", 
            'created_at'
        ]

    def get_address(self, obj):
        try:
            return ast.literal_eval(obj.address) if obj.address else {}
        except Exception:
            return {}

    def get_shipping(self, obj):
        try:
            return ast.literal_eval(obj.shipping) if obj.shipping else {}
        except Exception:
            return {}

class DiscountValidateSerializer(serializers.ModelSerializer):
    discount_amount = serializers.FloatField(read_only=True)
    final_total = serializers.FloatField(read_only=True)
    message = serializers.CharField(read_only=True)
    valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Discount
        fields = [
            "code",
            "discount_type",
            "value",
            "discount_amount",
            "final_total",
            "message",
            "valid",
        ]
