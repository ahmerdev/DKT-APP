from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
import ast
from .models import Category, Brand, Product, Discount, Redeem, Banner, Hero, Ad, ProductImage, ProductVariant, Order, OrderItem, Payment, AppUser, Address

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'created_at']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'image', 'created_at']      


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
        fields = ["id", "sku", "price", "stock", "attributes", "image"]



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

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "image",
            "regular_price",
            "sale_price",
            "SKU",
            "quantity",
            "stock_status",
            "points",
            "product_type",
            "category",
            "brand",
            "gallery_images",
            "variants",
            "created_at",
            "updated_at",
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['image', 'name', 'pts', 'variants', 'price', 'quantity']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['method', 'status']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'state', 'postal_code', 'country']



class AppUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=True)
    password_hash = serializers.CharField(read_only=True)
    total_points = serializers.SerializerMethodField()
    addresses = AddressSerializer(many=True, required=False) 

    class Meta:
        model = AppUser
        fields = ["id", "number", "name", "email", "image", "password", "password_hash",
                  "created_at", "api_token", "total_points", "addresses"]
        read_only_fields = ["id", "created_at", "password_hash", "api_token", "total_points"]

    # phone number validate
    def validate_number(self, value):
        import re
        if not re.fullmatch(r"\+?\d{9,15}", value):
            raise serializers.ValidationError("Enter a valid phone number (digits only, optional +, 9-15 chars).")
        return value

    # create user with password hash
    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        addresses_data = validated_data.pop("addresses", None)
        password = validated_data.pop("password")
        validated_data["password_hash"] = make_password(password)
        user = super().create(validated_data)

        # create addresses if provided
        if addresses_data:
            for addr_data in addresses_data:
                Address.objects.create(user=user, **addr_data)
        return user

    # update user and addresses
    def update(self, instance, validated_data):
        from django.contrib.auth.hashers import make_password

        # Update user fields
        instance.name = validated_data.get("name", instance.name)
        instance.email = validated_data.get("email", instance.email)
        instance.image = validated_data.get("image", instance.image)
        instance.save()


        return instance

    # Method to calculate total points
    def get_total_points(self, obj):
        normal_pts = (
            Order.objects.filter(user=obj, type="normal", status="delivered")
            .aggregate(total=Sum("items__pts"))["total"]
            or 0
        )
        redeem_pts = (
            Order.objects.filter(user=obj, type="redeem", status="delivered")
            .aggregate(total=Sum("items__pts"))["total"]
            or 0
        )
        return normal_pts - redeem_pts


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
        fields = [ 'id', 'user_detail', 'address', 'shipping', 'status', 'type', 'items', 'payments',
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