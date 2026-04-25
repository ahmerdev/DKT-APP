from django.shortcuts import get_object_or_404
import json
import secrets
import base64
import requests
import random
from django.core.cache import cache
import time
from .sms import send_sms
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework import status
from twilio.rest import Client
from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Product, PointSetting, UsedCoupon, Redeem, Category, Brand, Banner, Rider, Ad, Hero, Order, OrderItem, Payment, AppUser, Address, Privacy, About, ContactInfo, ContactForm, Review, Discount
from .serializers import CategorySerializer, RiderSerializer, RiderOrderSerializer, AppUserRegisterStepOneSerializer, AppUserRegisterStepTwoSerializer, DiscountValidateSerializer, BrandSerializer, BannerSerializer, HeroSerializer, PrivacySerializer, AboutSerializer, ContactInfoSerializer, ReviewSerializer, ContactFormSerializer, AdSerializer, ProductSerializer, RedeemSerializer, OrderSerializer, AppUserSerializer, AddressSerializer

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# Temporary OTP storage (in-memory)
otp_store = {}  # Format: { "number": { "otp": "123456", "timestamp": 1234567890 } }

# Step 1: Generate OTP
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    number = request.data.get("number")
    if not number:
        return Response({"error": "Phone number is required"}, status=400)

    if not AppUser.objects.filter(number=number).exists():
        if number.startswith("+92"):
            local_number = "0" + number[3:]
            if not AppUser.objects.filter(number=local_number, is_verified=True).exists():
                return Response({"error": "User not found"}, status=404)
            number = local_number  # local format use karo
        else:

            return Response({"error": "User not found"}, status=404)

    otp = str(random.randint(1000, 9999))
    cache.set(f"forgot_otp_{number}", otp, timeout=300)  # 5 min valid

    send_sms(number, f"Your OTP is {otp}")

    return Response({"message": "OTP sent"}, status=200)


# Step 2: Verify OTP + New Password
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    number = request.data.get("number")
    otp = request.data.get("otp")
    new_password = request.data.get("new_password")

    if not all([number, otp, new_password]):
        return Response({"error": "number, otp aur new_password required hain"}, status=400)

    cached_otp = cache.get(f"forgot_otp_{number}")

    if not cached_otp:
        return Response({"error": "OTP expired"}, status=400)

    if cached_otp != otp:
        return Response({"error": "Invalid OTP"}, status=400)

    try:
        user = AppUser.objects.get(number=number)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    from django.contrib.auth.hashers import make_password
    user.password_hash = make_password(new_password)
    user.save()

    cache.delete(f"forgot_otp_{number}")

    return Response({"message": "Password reset successfully"}, status=200)



#Mobile App User Creation API
@api_view(["POST"])
@permission_classes([AllowAny])
def create_app_user(request):

    serializer = AppUserRegisterStepOneSerializer(data=request.data)
    if serializer.is_valid():
        number = serializer.validated_data["number"]

        # Already registered check
        if AppUser.objects.filter(number=number, is_verified=True).exists():
            return Response({"error": "Number already registered"}, status=400)

        otp = str(random.randint(1000, 9999))
        cache.set(f"otp_{number}", otp, timeout=300)  

        send_sms(number, f"Your OTP is {otp}")
        return Response({"message": "OTP sent", "number": number}, status=200)
    return Response(serializer.errors, status=400)


# Helper function (Top par rakh do)
def get_point_settings():
    setting = PointSetting.objects.first()
    if not setting:
        setting = PointSetting(registration_bonus_points=settings.REGISTRATION_BONUS, point_value=settings.POINT_VALUE)
    return setting

@api_view(["POST"])
@permission_classes([AllowAny])
def complete_profile(request):
    number = request.data.get("number")
    temp_token = request.data.get("temp_token")

    cached_token = cache.get(f"verified_{number}")
    if not cached_token or cached_token != temp_token:
        return Response({"error": "Invalid or expired token"}, status=400)

    serializer = AppUserRegisterStepTwoSerializer(data=request.data)
    if serializer.is_valid():
        from django.contrib.auth.hashers import make_password

        points_to_add = get_point_settings().registration_bonus_points
        user = AppUser.objects.create(
            number=number,
            name=serializer.validated_data.get("name"),
            email=serializer.validated_data.get("email"),
            password_hash=make_password(serializer.validated_data.get("password")),
            is_verified=True,
            api_token=secrets.token_urlsafe(32),
            points=points_to_add  
        )

        cache.delete(f"verified_{number}")

        return Response({
            "id": user.id,
            "number": user.number,
            "name": user.name,
            "email": user.email,
            "points": user.points,
            "api_token": user.api_token,
            "created_at": user.created_at,
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    number = request.data.get("number")
    otp = request.data.get("otp")

    cached_otp = cache.get(f"otp_{number}")

    if cached_otp is None:
        return Response({"error": "OTP expired"}, status=400)

    if cached_otp != otp:
        return Response({"error": "Invalid OTP"}, status=400)

    temp_token = secrets.token_urlsafe(32)
    cache.set(f"verified_{number}", temp_token, timeout=600)  

    cache.delete(f"otp_{number}")

    return Response({
        "message": "OTP verified. Please complete your profile.",
        "temp_token": temp_token,
        "number": number
    })
    



@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    number = request.data.get("number")

    if not number:
        return Response({"error": "Number is required"}, status=400)

    if AppUser.objects.filter(number=number, is_verified=True).exists():
        return Response({"error": "Number already registered"}, status=400)

    otp = str(random.randint(1000, 9999))
    cache.set(f"otp_{number}", otp, timeout=300)

    send_sms(number, f"Your OTP is {otp}")

    return Response({"message": "OTP resent"})


# Active & Deactive
@api_view(['PUT'])
@permission_classes([AllowAny])
def deactivate_account(request, pk):
    user = get_object_or_404(AppUser, pk=pk)  
    user.is_active = False
    user.save()
    
    return Response(
        {'message': f'User {user.number} has been deactivated successfully.'},
        status=status.HTTP_200_OK
    )

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
            "is_active": user.is_active,
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


# Mobile App Privacy API
@api_view(['GET'])
def privacy_content_api(request):
    privacy = Privacy.objects.all().order_by('-id')
    serializer = PrivacySerializer(privacy, many=True, context={'request': request})
    return Response(serializer.data)


# Mobile App About API
@api_view(['GET'])
def about_content_api(request):
    about = About.objects.all().order_by('-id')
    serializer = AboutSerializer(about, many=True, context={'request': request})
    return Response(serializer.data)


# Mobile App About API
@api_view(['GET'])
def contact_content_api(request):
    contact = ContactInfo.objects.all().order_by('-id')
    serializer = ContactInfoSerializer(contact, many=True, context={'request': request})
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


@api_view(['POST'])
def create_review(request):
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "success": True,
            "message": "Review submitted successfully!",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        "success": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_contact(request):
    serializer = ContactFormSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "success": True,
            "message": "Contact form submitted successfully!",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        "success": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# @api_view(["POST"])
# @permission_classes([AllowAny])   
# def create_order(request): 
#     data = request.data
#     user_id = data.get("user_id")
#     applied_points = int(data.get("applied_points", 0)) 

#     try:
#         app_user = AppUser.objects.get(id=user_id)
#     except AppUser.DoesNotExist:
#         return Response({"error": "Invalid user_id"}, status=400)
    
#     with transaction.atomic():
    
#             points_discount = 0.00
#             if applied_points > 0:
#                 if applied_points > app_user.points:
#                     return Response({"error": f"Insufficient points. You have {app_user.points}, requested {applied_points}."}, status=400)
                
#                 settings = get_point_settings()
#                 points_discount = applied_points * settings.point_value

#                 app_user.points = (app_user.points or 0) - applied_points
#                 app_user.save(update_fields=["points"])

#             order = Order.objects.create(
#                 user=app_user,   
#                 address=data.get("address", ""),
#                 shipping=data.get("shipping", ""),
#                 status=data.get("status", "pending"),
#                 points_used=applied_points,
#                 points_discount=points_discount
#             )

#             for item in data.get("product", []):
#                 image_data = item.get("image")
#                 image_file = None

#                 if isinstance(image_data, dict):
#                     image_data = image_data.get("uri")

#                 # 1. Base64 image
#                 if image_data and isinstance(image_data, str) and image_data.startswith("data:image"):
#                     format, imgstr = image_data.split(";base64,")
#                     ext = format.split("/")[-1]
#                     image_file = ContentFile(base64.b64decode(imgstr), name=f"order_item.{ext}")

#                 # 2. File object (direct upload)
#                 elif image_data and not isinstance(image_data, str):
#                     image_file = image_data

#                 # 3. Agar URL aaya hai
#                 elif image_data and isinstance(image_data, str) and image_data.startswith("http"):
#                     try:
#                         response = requests.get(image_data)
#                         if response.status_code == 200:
#                             ext = image_data.split(".")[-1].split("?")[0]
#                             image_file = ContentFile(response.content, name=f"order_item.{ext}")
#                     except Exception as e:
#                         print("Image download failed:", e)

#                 OrderItem.objects.create(
#                     order=order,
#                     image=image_file, 
#                     name=item.get("name"),
#                     pts=item.get("pts", 0),
#                     variants=item.get("variants", ""),
#                     price=item.get("price", 0),
#                     cost_price=item.get("cost_price", 0),
#                     quantity=item.get("quantity", 1),
#                 )

#             # Payment loop
#             for pay in data.get("payment", []):
#                 Payment.objects.create(
#                     order=order,
#                     method=pay.get("method", "Unknown"),
#                     status=pay.get("status", "Pending"),
#                 )

#             return Response(
#                 {
#                     "message": "Order created successfully",
#                     "order": OrderSerializer(order).data,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )
    

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from decimal import Decimal, ROUND_DOWN
import base64
import requests
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Order, OrderItem, Payment, Discount, AppUser


# ══════════════════════════════════════
# ORDER LIST
# ══════════════════════════════════════
@api_view(["GET"])
def list_orders(request):
    orders = Order.objects.all().order_by("-created_at")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import requests
import base64


def _validate_and_calculate_coupon(discount, user, items_data):
    now = timezone.now()

    # 1. Basic Date & Active Check
    if not discount.active:
        return {"valid": False, "message": "Coupon is inactive."}
    if discount.start_date and discount.start_date > now:
        return {"valid": False, "message": "Coupon is not active yet."}
    if discount.end_date and discount.end_date < now:
        return {"valid": False, "message": "Coupon has expired."}

    # 2. SPECIFIC USER CHECK
    if not discount.apply_all_users:
        if not user:
            return {"valid": False, "message": "Login required to use this coupon."}
        if not discount.users.filter(id=user.id).exists():
            return {"valid": False, "message": "This coupon is not valid for your account."}

    # 3. ONE-TIME USE CHECK
    if user is not None and UsedCoupon.objects.filter(user=user, discount=discount).exists():
        return {"valid": False, "message": "You have already used this coupon."}

    # 4. CALCULATION & PRODUCT CHECK
    discount_value = Decimal(str(discount.value))
    is_percent = discount.discount_type == Discount.PERCENTAGE
    discount_amount = Decimal("0.00")
    final_total = Decimal("0.00")
    applied_product_ids = []

    # ✅ FIX: items_data ke saare IDs ko int mein convert karo
    def safe_int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    if discount.apply_all_products:
        cart_total = sum(
            Decimal(str(item.get("price", 0))) * Decimal(str(item.get("quantity", 1)))
            for item in items_data
        )
        applied_product_ids = [safe_int(item.get("id")) for item in items_data]

        if is_percent:
            discount_amount = (cart_total * discount_value / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        else:
            discount_amount = min(discount_value, cart_total).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        final_total = (cart_total - discount_amount).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    else:
        # ✅ FIX: eligible_product_ids already integers hain DB se
        eligible_product_ids = set(discount.products.values_list('id', flat=True))
        eligible_items = []
        non_eligible_items = []

        for item in items_data:
            # ✅ FIX: string "39" → int 39 karke compare karo
            prod_id = safe_int(item.get("id"))
            if prod_id and prod_id in eligible_product_ids:
                eligible_items.append(item)
            else:
                non_eligible_items.append(item)

        if not eligible_items:
            return {"valid": False, "message": "This coupon is only valid for specific products."}

        applied_product_ids = [safe_int(item.get("id")) for item in eligible_items]

        eligible_total = sum(
            Decimal(str(item.get("price", 0))) * Decimal(str(item.get("quantity", 1)))
            for item in eligible_items
        )
        non_eligible_total = sum(
            Decimal(str(item.get("price", 0))) * Decimal(str(item.get("quantity", 1)))
            for item in non_eligible_items
        )

        if is_percent:
            discount_amount = (eligible_total * discount_value / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        else:
            discount_amount = min(discount_value, eligible_total).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        final_total = (eligible_total - discount_amount + non_eligible_total).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    if final_total < 0:
        final_total = Decimal("0.00")

    return {
        "valid": True,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "applied_product_ids": applied_product_ids
    }


@api_view(['POST'])
def validate_discount_api(request):
    code = request.data.get("code", "").strip()
    items = request.data.get("items", [])
    user_id = request.data.get("user_id")
    phone = request.data.get("phone")  # ✅ phone bhi lo

    if not code:
        return Response({"valid": False, "message": "Coupon code is required."}, status=400)
    if not items:
        return Response({"valid": False, "message": "No items provided."}, status=400)

    try:
        discount = Discount.objects.get(code__iexact=code)
    except Discount.DoesNotExist:
        return Response({"valid": False, "message": "Invalid coupon code."}, status=404)

    # ✅ user_id se ya phone se user dhundo
    user = None
    if user_id:
        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response({"valid": False, "message": "Invalid user."}, status=400)
    elif phone:
        try:
            user = AppUser.objects.get(number=phone)  # ya jो bhi phone field ka naam hai
        except AppUser.DoesNotExist:
            return Response({"valid": False, "message": "User not found."}, status=400)

    result = _validate_and_calculate_coupon(discount, user, items)

    if not result["valid"]:
        return Response(result, status=400)

    return Response({
        "valid": True,
        "code": discount.code,
        "discount_type": discount.discount_type,
        "value": float(discount.value),
        "discount_amount": float(result["discount_amount"]),
        "final_total": float(result["final_total"]),
        "applied_product_ids": result["applied_product_ids"],
        "message": "Coupon applied successfully!"
    }, status=200)



@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    data = request.data
    user_id = data.get("user_id")
    applied_points = int(data.get("applied_points", 0))
    discount_code = data.get("discount_code", "").strip() if data.get("discount_code") else None

    try:
        app_user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return Response({"error": "Invalid user_id"}, status=400)

    try:
        with transaction.atomic():

            # ── Points Logic ──
             points_discount = Decimal("0.00")

        if applied_points > 0:
            if applied_points > (app_user.points or 0):
                return Response({
                    "error": f"Insufficient points. You have {app_user.points}, requested {applied_points}."
                }, status=400)

            settings = get_point_settings()
            points_discount = Decimal(applied_points) * Decimal(settings.point_value)

            app_user.points = (app_user.points or 0) - applied_points
            app_user.save(update_fields=["points"])

            # ── Coupon Validation ──
            discount_obj = None
            discount_amount = Decimal("0.00")
            products_data = data.get("product", [])

            if discount_code:
                try:
                    discount_obj = Discount.objects.get(code__iexact=discount_code)

                    # FIX: id properly lo aur int karo
                    items_for_validation = []
                    for item in products_data:
                        item_id = item.get("id") or item.get("product_id")

                        # FIX: string to int
                        try:
                            item_id = int(item_id) if item_id is not None else None
                        except (ValueError, TypeError):
                            item_id = None

                        # agar id nahi toh name se dhundo
                        if not item_id and item.get("name"):
                            try:
                                from .models import Product
                                product = Product.objects.filter(name=item.get("name")).first()
                                if product:
                                    item_id = product.id
                            except:
                                pass

                        items_for_validation.append({
                            "id": item_id,
                            "price": item.get("price", 0),
                            "quantity": item.get("quantity", 1),
                        })

                    validation = _validate_and_calculate_coupon(
                        discount_obj,
                        app_user,
                        items_for_validation
                    )

                    if not validation["valid"]:
                        return Response({"error": validation["message"]}, status=400)

                    discount_amount = validation["discount_amount"]

                except Discount.DoesNotExist:
                    return Response({"error": "Invalid coupon code."}, status=400)

            # ── Create Order ──
            order = Order.objects.create(
                user=app_user,
                address=data.get("address", ""),
                shipping=data.get("shipping", ""),
                city_id=data.get("city"),
                status=data.get("status", "pending"),
                points_used=applied_points,
                points_discount=points_discount,
                discount_code=discount_code,
                discount_type=discount_obj.discount_type if discount_obj else "",
                discount_amount=discount_amount
            )

            # ── Create Order Items ──
            total = Decimal("0.00")

            for item in products_data:
                # ── Image Handling ──
                image_data = item.get("image")
                image_file = None
                if isinstance(image_data, dict):
                    image_data = image_data.get("uri")

                if image_data and isinstance(image_data, str):
                    if image_data.startswith("data:image"):
                        try:
                            format, imgstr = image_data.split(";base64,")
                            ext = format.split("/")[-1]
                            image_file = ContentFile(base64.b64decode(imgstr), name=f"order_item.{ext}")
                        except:
                            pass
                    elif image_data.startswith("http"):
                        try:
                            resp = requests.get(image_data, timeout=5)
                            if resp.status_code == 200:
                                ext = image_data.split(".")[-1].split("?")[0]
                                image_file = ContentFile(resp.content, name=f"order_item.{ext}")
                        except:
                            pass
                elif image_data and not isinstance(image_data, str):
                    image_file = image_data

                price = Decimal(str(item.get("price", 0)))
                qty = int(item.get("quantity", 1))
                total += price * qty

                #  FIX: product_id int karo
                product_id = item.get("id") or item.get("product_id")
                try:
                    product_id = int(product_id) if product_id is not None else None
                except (ValueError, TypeError):
                    product_id = None

                if not product_id and item.get("name"):
                    try:
                        from .models import Product
                        product = Product.objects.filter(name=item.get("name")).first()
                        if product:
                            product_id = product.id
                    except:
                        pass

                OrderItem.objects.create(
                    order=order,
                    product_id=product_id,
                    image=image_file,
                    name=item.get("name"),
                    pts=item.get("pts", 0),
                    variants=item.get("variants", ""),
                    price=price,
                    cost_price=item.get("cost_price", 0),
                    quantity=qty,
                )

            # ── Final Total ──
            final_total = total - discount_amount - points_discount
            if final_total < 0:
                final_total = Decimal("0.00")

            order.total_amount = final_total
            order.save(update_fields=["total_amount"])

            # ── Save Used Coupon ──
            if discount_obj:
                UsedCoupon.objects.create(
                    user=app_user,
                    discount=discount_obj,
                    order=order
                )
                Discount.objects.filter(id=discount_obj.id).update(used_count=F('used_count') + 1)

            # ── Payment Records ──
            for pay in data.get("payment", []):
                Payment.objects.create(
                    order=order,
                    method=pay.get("method", "Unknown"),
                    status=pay.get("status", "Pending"),
                )

            return Response({
                "message": "Order created successfully",
                "order": OrderSerializer(order).data
            }, status=201)

    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)




from django.db import transaction
from django.db.models import Sum, F

@api_view(["PATCH"])
def update_order_status(request, order_pk):
    try:
        order = Order.objects.select_related("user").get(id=order_pk)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get("status")

    if new_status not in dict(Order.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        if new_status == "delivered" and not order.is_points_added:
            if order.user:
                if order.type == "redeem":
                    pass
                else:
                    #  Normal —  earned add
                    earned = order.items.aggregate(total=Sum("pts"))["total"] or 0
                    if earned > 0:
                        AppUser.objects.filter(pk=order.user.pk).update(
                            points=F("points") + earned
                        )

            Order.objects.filter(id=order_pk).update(
                status=new_status,
                is_points_added=True
            )
        else:
            Order.objects.filter(id=order_pk).update(status=new_status)

    return Response({
        "message": "Status updated",
        "order": OrderSerializer(order).data
    })
    






@api_view(['PUT'])
@permission_classes([AllowAny])
def toggle_is_active(request, model_name, pk):

    model_map = {
        "product": Product,
        "category": Category,
        "brand": Brand,
        "rider": Rider,
    }

    if model_name not in model_map:
        return Response({"error": "Invalid model"}, status=400)

    obj = get_object_or_404(model_map[model_name], pk=pk)

    obj.is_active = not obj.is_active
    obj.save()

    status_text = "Activated" if obj.is_active else "Deactivated"

    return Response({
        "message": f"{model_name.title()} has been {status_text}",
        "status": obj.is_active,
        "status_text": status_text
    })

from django.db import transaction
from rest_framework.viewsets import ModelViewSet

class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all().order_by('position')  
    serializer_class = ProductSerializer


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by('position')
    serializer_class = CategorySerializer

class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all().order_by('position')
    serializer_class = BrandSerializer



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail


# ══════════════════════════════════════
# RIDER LOGIN API
# ══════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def rider_login_api(request):
    email = request.data.get("email", "").strip()
    password = request.data.get("password", "").strip()

    if not email or not password:
        return Response({"error": "Email and password required."}, status=400)

    try:
        rider = Rider.objects.get(email__iexact=email)

        if not rider.is_active:
            return Response({"error": "Your account is inactive."}, status=403)

        if rider.password.startswith("pbkdf2"):
            login_success = check_password(password, rider.password)
        else:
            login_success = (password == rider.password)

        if login_success:
            return Response({
                "message": f"Welcome {rider.name}",
                "rider": {
                    "id": rider.id,
                    "name": rider.name,
                    "email": rider.email,
                    "phone": rider.phone if hasattr(rider, 'phone') else "",
                    "is_active": rider.is_active,
                }
            }, status=200)
        else:
            return Response({"error": "Wrong password."}, status=400)

    except Rider.DoesNotExist:
        return Response({"error": "Rider not found."}, status=404)

from .models import Rider, RiderPasswordResetToken
# ══════════════════════════════════════
# RIDER FORGOT PASSWORD API
# ══════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def rider_forgot_password_api(request):
    email = request.data.get("email", "").strip()

    if not email:
        return Response({"error": "Email is required."}, status=400)

    try:
        rider = Rider.objects.get(email__iexact=email)

        # Purane tokens delete karo
        RiderPasswordResetToken.objects.filter(rider=rider).delete()

        # Naya token banao
        token_obj = RiderPasswordResetToken.objects.create(rider=rider)

        # Reset link banao
        reset_link = request.build_absolute_uri(
            f"/rider/reset-password/{token_obj.token}/"
        )

        send_mail(
            subject="Password Reset Request",
            message=f"Hi {rider.name},\n\nYour password reset link:\n{reset_link}\n\nThis link will expire in 1 hour.\n\nIf you did not request this, ignore this email.",
            from_email=None,
            recipient_list=[rider.email],
            fail_silently=False,
        )

        return Response({"message": "Reset link sent to your email."}, status=200)

    except Rider.DoesNotExist:
        return Response({"error": "No rider found with this email."}, status=404)


# ══════════════════════════════════════
# RIDER RESET PASSWORD API
# ══════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def rider_reset_password_api(request):
    token = request.data.get("token", "").strip()
    password = request.data.get("password", "").strip()
    confirm_password = request.data.get("confirm_password", "").strip()

    if not token or not password or not confirm_password:
        return Response({"error": "All fields are required."}, status=400)

    try:
        token_obj = RiderPasswordResetToken.objects.get(token=token)
    except RiderPasswordResetToken.DoesNotExist:
        return Response({"error": "Invalid reset token."}, status=400)

    if not token_obj.is_valid():
        return Response({"error": "Reset link expired. Please request again."}, status=400)

    if password != confirm_password:
        return Response({"error": "Passwords do not match."}, status=400)

    if len(password) < 6:
        return Response({"error": "Password must be at least 6 characters."}, status=400)

    rider = token_obj.rider
    rider.password = make_password(password)
    rider.save()

    token_obj.is_used = True
    token_obj.save()

    return Response({"message": "Password reset successful! Please login."}, status=200)


# ══════════════════════════════════════
# RIDER ORDERS API (Assigned Orders)
# ══════════════════════════════════════
@api_view(["GET"])
@permission_classes([AllowAny])
def rider_orders_api(request, rider_id):
    try:
        rider = Rider.objects.get(id=rider_id)
    except Rider.DoesNotExist:
        return Response({"error": "Rider not found."}, status=404)

    orders = Order.objects.filter(rider=rider).order_by("-id")

    return Response({
        "rider": RiderSerializer(rider).data,
        "orders": RiderOrderSerializer(orders, many=True).data  
    }, status=200)


# ══════════════════════════════════════
# RIDER ORDER STATUS UPDATE API
# ══════════════════════════════════════
# @api_view(["POST"])
# @permission_classes([AllowAny])
# def rider_update_order_status_api(request, order_id):
#     rider_id = request.data.get("rider_id")
#     status = request.data.get("status", "").strip()

#     ALLOWED_STATUSES = ["pending", "on_the_way", "delivered", "cancelled"]

#     if not rider_id:
#         return Response({"error": "rider_id required."}, status=400)

#     if status not in ALLOWED_STATUSES:
#         return Response({
#             "error": f"Invalid status. Allowed: {', '.join(ALLOWED_STATUSES)}"
#         }, status=400)

#     try:
#         rider = Rider.objects.get(id=rider_id)
#     except Rider.DoesNotExist:
#         return Response({"error": "Rider not found."}, status=404)

#     try:
#         order = Order.objects.get(id=order_id, rider=rider)
#     except Order.DoesNotExist:
#         return Response({"error": "Order not found or not assigned to you."}, status=404)

#     order.status = status
#     order.save(update_fields=["status"])

#     return Response({
#         "message": "Order status updated successfully.",
#         "order_id": order.id,
#         "status": order.status,
#     }, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
def rider_update_order_status_api(request, order_id):
    rider_id = request.data.get("rider_id")
    status = request.data.get("status", "").strip()
    cancel_reason = request.data.get("cancel_reason", "").strip()

    ALLOWED_STATUSES = ["pending", "on_the_way", "delivered", "cancelled"]

    if not rider_id:
        return Response({"error": "rider_id required."}, status=400)

    if status not in ALLOWED_STATUSES:
        return Response({
            "error": f"Invalid status. Allowed: {', '.join(ALLOWED_STATUSES)}"
        }, status=400)

    if status == "cancelled" and not cancel_reason:
        return Response({"error": "Please provide a reason for cancellation."}, status=400)

    try:
        order = Order.objects.get(id=order_id, rider_id=rider_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or not assigned to you."}, status=404)

    if order.status in ["delivered", "cancelled"]:
        return Response({
            "error": f"Order is already {order.status}. No further changes allowed."
        }, status=400)

    try:
        rider = Rider.objects.get(id=rider_id)
    except Rider.DoesNotExist:
        return Response({"error": "Rider not found."}, status=404)

    order.status = status

    if status == "cancelled":
        order.cancel_reason = cancel_reason

    if status == "delivered" and not order.is_points_added:
        from django.db.models import Sum, F
        if order.user and order.type != "redeem":
            earned = order.items.aggregate(total=Sum("pts"))["total"] or 0
            if earned > 0:
                AppUser.objects.filter(pk=order.user.pk).update(
                    points=F("points") + earned
                )
        order.is_points_added = True

    order.save()

    return Response({
        "message": "Order status updated successfully.",
        "order_id": order.id,
        "status": order.status,
        "cancel_reason": order.cancel_reason if status == "cancelled" else None,
    }, status=200)
