from django.shortcuts import get_object_or_404
import json
import secrets
import base64
import requests
from django.utils import timezone
from rest_framework import status
from twilio.rest import Client
from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Product, Redeem, Category, Brand, Banner, Ad, Hero, Order, OrderItem, Payment, AppUser, Address, Discount
from .serializers import CategorySerializer, DiscountValidateSerializer, BrandSerializer, BannerSerializer, HeroSerializer, AdSerializer, ProductSerializer, RedeemSerializer, OrderSerializer, AppUserSerializer, AddressSerializer

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


#Mobile App User Creation API
@api_view(["POST"])
@permission_classes([AllowAny])
def create_app_user(request):
    serializer = AppUserSerializer(data=request.data)
    if serializer.is_valid():
        instance = serializer.save()
        # generate api token for app login
        instance.api_token = secrets.token_urlsafe(32)
        instance.save(update_fields=["api_token"])
        return Response({
            "id": instance.id,
            "number": instance.number,
            "created_at": instance.created_at,
            "api_token": instance.api_token
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Mobile App User Update Profile API
@api_view(["PUT", "PATCH"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser]) 
def update_profile_view(request, user_pk):
    try:
        user = AppUser.objects.get(pk=user_pk)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = AppUserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()  

        return Response({
           "id": user.id,
            "number": user.number,
            "name": user.name,
            "email": user.email,
            "image": request.build_absolute_uri(user.image.url) if user.image else None,
            "created_at": user.created_at,
            "api_token": user.api_token,
            "addresses": AddressSerializer(user.addresses.all(), many=True).data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"])
@permission_classes([AllowAny])
def create_user_address(request, pk):
    try:
        user = AppUser.objects.get(pk=pk)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get address data
    addresses = request.data.get("addresses", [])

    # If data is stringified JSON, parse it
    if isinstance(addresses, str):
        try:
            addresses = json.loads(addresses)
        except json.JSONDecodeError:
            return Response({"error": "Invalid address format"}, status=status.HTTP_400_BAD_REQUEST)

    # If a single address object is sent, wrap it in a list
    if isinstance(addresses, dict):
        addresses = [addresses]

    # Create new address records
    created_addresses = []
    for addr in addresses:
        serializer = AddressSerializer(data=addr)
        if serializer.is_valid():
            serializer.save(user=user)
            created_addresses.append(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "message": "Address(es) added successfully",
        "addresses": created_addresses
    }, status=status.HTTP_201_CREATED)

#Mobile App User Login API
@api_view(["POST"])
@permission_classes([AllowAny])
def app_user_login(request):
    number = request.data.get("number")
    password = request.data.get("password")

    if not number or not password:
        return Response({"detail": "Number and password required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AppUser.objects.get(number=number)
    except AppUser.DoesNotExist:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    if check_password(password, user.password_hash):
        # generate new token each login if you like
        if not user.api_token:
            user.api_token = secrets.token_urlsafe(32)
            user.save(update_fields=["api_token"])
        return Response({
            "id": user.id,
            "number": user.number,
            "api_token": user.api_token
        }, status=status.HTTP_200_OK)
    else:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


#Mobile App User List API
@api_view(["GET"])
def app_user_list(request):
    users = AppUser.objects.all().order_by("-created_at")
    serializer = AppUserSerializer(users, many=True)
    return Response(serializer.data)


#Mobile App User Delete API
@api_view(["DELETE"])
def account_delete(request, pk):
    user = get_object_or_404(AppUser, pk=pk)
    user.delete()
    return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(["DELETE"])
def delete_user_address(request, pk):
    address = get_object_or_404(Address, pk=pk)
    address.delete()
    return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# Mobile App Category API
@api_view(['GET'])
def category_list_api(request):
    categories = Category.objects.all().order_by('-id')
    serializer = CategorySerializer(categories, many=True, context={'request': request})
    return Response(serializer.data)

# Mobile App Brand API
@api_view(['GET'])
def brand_list_api(request):
    brands = Brand.objects.all().order_by('-id')
    serializer = BrandSerializer(brands, many=True, context={'request': request})
    return Response(serializer.data)

# Mobile App Banner API
@api_view(['GET'])
def banner_list_api(request):
    banners = Banner.objects.all().order_by('-id')
    serializer = BannerSerializer(banners, many=True, context={'request': request})
    return Response(serializer.data)


# Mobile App Ads API
@api_view(['GET'])
def ad_list_api(request):
    ads = Ad.objects.all().order_by('-id')
    serializer = AdSerializer(ads, many=True, context={'request': request})
    return Response(serializer.data)


# Mobile App Hero API
@api_view(['GET'])
def hero_list_api(request):
    heros = Hero.objects.all().order_by('-id')
    serializer = HeroSerializer(heros, many=True, context={'request': request})
    return Response(serializer.data)


# Mobile App Product API
@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.all().order_by('-id')
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


# Mobile App Redeem API
@api_view(['GET'])
def redeem_list_api(request):
    redeems = Redeem.objects.all().order_by('-id')
    serializer = RedeemSerializer(redeems, many=True, context={'request': request})
    return Response(serializer.data)




@api_view(["POST"])
@permission_classes([AllowAny])   
def create_order(request): 
    data = request.data
    user_id = data.get("user_id")
    try:
        app_user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return Response({"error": "Invalid user_id"}, status=400)

    order = Order.objects.create(
        user=app_user,   
        address=data.get("address", ""),
        shipping=data.get("shipping", ""),
        status=data.get("status", "pending"),
    )

    for item in data.get("product", []):
        image_data = item.get("image")
        image_file = None

        if isinstance(image_data, dict):
            image_data = image_data.get("uri")

        # 1. Base64 image
        if image_data and isinstance(image_data, str) and image_data.startswith("data:image"):
            format, imgstr = image_data.split(";base64,")
            ext = format.split("/")[-1]
            image_file = ContentFile(base64.b64decode(imgstr), name=f"order_item.{ext}")

        # 2. File object (direct upload)
        elif image_data and not isinstance(image_data, str):
            image_file = image_data

        # 3. Agar URL aaya hai
        elif image_data and isinstance(image_data, str) and image_data.startswith("http"):
            try:
                response = requests.get(image_data)
                if response.status_code == 200:
                    ext = image_data.split(".")[-1].split("?")[0]
                    image_file = ContentFile(response.content, name=f"order_item.{ext}")
            except Exception as e:
                print("Image download failed:", e)

        OrderItem.objects.create(
            order=order,
            image=image_file, 
            name=item.get("name"),
            pts=item.get("pts", 0),
            variants=item.get("variants", ""),
            price=item.get("price", 0),
            quantity=item.get("quantity", 1),
        )

    # Payment loop
    for pay in data.get("payment", []):
        Payment.objects.create(
            order=order,
            method=pay.get("method", "Unknown"),
            status=pay.get("status", "Pending"),
        )

    return Response(
        {
            "message": "Order created successfully",
            "order": OrderSerializer(order).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
def update_order_status(request, order_pk):
    try:
        order = Order.objects.get(id=order_pk)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get("status")

    if new_status not in dict(Order.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    order.status = new_status
    order.save()

    return Response({
        "message": "Status updated",
        "order": OrderSerializer(order).data
    })


@api_view(["GET"])
def list_orders(request):
    orders = Order.objects.all().order_by("-created_at")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


# from decimal import Decimal
# from django.utils import timezone
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Discount


# @api_view(['POST'])
# def validate_discount_api(request):
#     code = request.data.get("code")
#     total = request.data.get("total")
#     product_ids = request.data.get("products", [])  
#     items = request.data.get("items", [])
    

#     # Validate code
#     if not code:
#         return Response({"valid": False, "message": "Coupon code is required."}, status=400)

#     # Validate total
#     try:
#         total = Decimal(str(total or 0))
#     except Exception:
#         return Response({"valid": False, "message": "Invalid total amount."}, status=400)

#     # Check if coupon exists
#     try:
#         discount = Discount.objects.get(code__iexact=code)
#     except Discount.DoesNotExist:
#         return Response({"valid": False, "message": "Invalid coupon code."}, status=404)

#     #  Handle date comparison properly
#     now = timezone.now()
#     start_date = discount.start_date
#     end_date = discount.end_date

#     if start_date and start_date > now:
#         return Response({"valid": False, "message": "Coupon not active yet."}, status=400)
#     if end_date and end_date < now:
#         return Response({"valid": False, "message": "Coupon expired."}, status=400)

#     # Product
#     if not discount.apply_all_products:
#         if not product_ids:
#             return Response({"valid": False, "message": "No products provided for coupon."}, status=400)
#         allowed_products = discount.products.filter(id__in=product_ids)
#         if not allowed_products.exists():
#             return Response({"valid": False, "message": "Coupon not valid for these products."}, status=400)



#      # ------------------------
#     # Product eligibility
#     # ------------------------
#     applied_product_ids = []

#     if not discount.apply_all_products:
#         if not product_ids:
#             return Response({"valid": False, "message": "No products provided for coupon."}, status=400)

#         allowed_products = discount.products.filter(id__in=product_ids)
#         if not allowed_products.exists():
#             return Response({"valid": False, "message": "Coupon not valid for these products."}, status=400)

#         allowed_ids = list(allowed_products.values_list("id", flat=True))
#         applied_product_ids = allowed_ids

#         # eligible and non-eligible totals
#         eligible_total = sum(
#             Decimal(str(item.get("price", 0))) * int(item.get("quantity", 1))
#             for item in items
#             if item.get("id") in allowed_ids
#         )
#         non_eligible_total = sum(
#             Decimal(str(item.get("price", 0))) * int(item.get("quantity", 1))
#             for item in items
#             if item.get("id") not in allowed_ids
#         )

#         # discount only on eligible products
#         discount_value = Decimal(discount.value)
#         if discount.discount_type == "percent":
#             discount_amount = eligible_total * (discount_value / Decimal(100))
#         else:
#             discount_amount = min(discount_value, eligible_total)

#         # final total = non-eligible + (eligible - discount)
#         final_total = non_eligible_total + (eligible_total - discount_amount)

#     else:
#         # coupon applies to all products
#         discount_value = Decimal(discount.value)
#         if discount.discount_type == "percent":
#             discount_amount = total * (discount_value / Decimal(100))
#         else:
#             discount_amount = min(discount_value, total)
#         final_total = total - discount_amount
#         applied_product_ids = product_ids  

#     if final_total < 0:
#         final_total = Decimal("0.00")

#     # ------------------------
#     # Response
#     # ------------------------
#     response_data = {
#         "valid": True,
#         "code": discount.code,
#         "discount_type": discount.discount_type,
#         "value": float(discount.value),
#         "discount_amount": round(float(discount_amount), 2),
#         "final_total": round(float(final_total), 2),
#         "applied_product_ids": applied_product_ids,
#         "message": "Coupon applied successfully!",
#     }

#     return Response(response_data, status=status.HTTP_200_OK)


from decimal import Decimal, ROUND_DOWN
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Discount

@api_view(['POST'])
def validate_discount_api(request):
    code = request.data.get("code")
    total = request.data.get("total")
    product_ids = request.data.get("products", [])  
    items = request.data.get("items", [])

    # Validate code
    if not code:
        return Response({"valid": False, "message": "Coupon code is required."}, status=400)

    # Validate total
    try:
        total = Decimal(str(total or 0))
    except Exception:
        return Response({"valid": False, "message": "Invalid total amount."}, status=400)

    # Check if coupon exists
    try:
        discount = Discount.objects.get(code__iexact=code)
    except Discount.DoesNotExist:
        return Response({"valid": False, "message": "Invalid coupon code."}, status=404)

    # Check dates
    now = timezone.now()
    if discount.start_date and discount.start_date > now:
        return Response({"valid": False, "message": "Coupon not active yet."}, status=400)
    if discount.end_date and discount.end_date < now:
        return Response({"valid": False, "message": "Coupon expired."}, status=400)

    # Initialize
    applied_product_ids = []
    eligible_total = Decimal("0.00")
    non_eligible_total = Decimal("0.00")
    discount_amount = Decimal("0.00")
    final_total = Decimal("0.00")

    if not discount.apply_all_products:
        if not product_ids:
            return Response({"valid": False, "message": "No products provided for coupon."}, status=400)

        eligible_items = [
            item for item in items
            if item.get("id") in [p.id for p in discount.products.all()]
        ]

        applied_product_ids = [item.get("id") for item in eligible_items]

        # Calculate totals
        eligible_total = sum(
            Decimal(str(item.get("price", 0))) * Decimal(str(item.get("quantity", 1)))
            for item in eligible_items
        )

        non_eligible_total = sum(
            Decimal(str(item.get("price", 0))) * Decimal(str(item.get("quantity", 1)))
            for item in items
            if item.get("id") not in applied_product_ids
        )

        discount_value = Decimal(str(discount.value))
        if discount.discount_type.lower() in ["percent", "percentage"]:
            discount_amount = (eligible_total * discount_value / Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        else:
            discount_amount = min(discount_value, eligible_total).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        final_total = (eligible_total - discount_amount + non_eligible_total).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    else:
        # Coupon applies to all products
        applied_product_ids = product_ids
        total = Decimal(str(total))
        discount_value = Decimal(str(discount.value))
        if discount.discount_type.lower() in ["percent", "percentage"]:
            discount_amount = (total * discount_value / Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        else:
            discount_amount = min(discount_value, total).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        final_total = (total - discount_amount).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    if final_total < 0:
        final_total = Decimal("0.00")

    response_data = {
        "valid": True,
        "code": discount.code,
        "discount_type": discount.discount_type,
        "value": float(discount.value),
        "discount_amount": float(discount_amount),
        "final_total": float(final_total),
        "applied_product_ids": applied_product_ids,
        "message": "Coupon applied successfully!"
    }

    return Response(response_data, status=status.HTTP_200_OK)
