import json
import re
import base64
import random
import secrets

import requests

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.validators import validate_email
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from decimal import Decimal, ROUND_DOWN

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from twilio.rest import Client

from .sms import send_sms
from .models import (
    Product, PointSetting, UsedCoupon, DiscountPopup, Redeem, Category, Brand,
    Banner, Rider, RiderPasswordResetToken, Ad, Hero, Order, OrderItem, Payment,
    AppUser, Address, Privacy, About, ContactInfo, ContactForm, Review, Discount,
)
from .serializers import (
    CategorySerializer, DiscountPopupSerializer, RiderSerializer, RiderOrderSerializer,
    DiscountValidateSerializer, BrandSerializer, BannerSerializer, HeroSerializer,
    PrivacySerializer, AboutSerializer, ContactInfoSerializer, ReviewSerializer,
    ContactFormSerializer, AdSerializer, ProductSerializer, RedeemSerializer,
    OrderSerializer, AppUserSerializer, AddressSerializer,
)

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# ═══════════════════════════════════════════════════════════════
# OTP HELPERS
# A single OTP is generated and delivered to both the phone number
# and the email address. The user can verify with either one.
# ═══════════════════════════════════════════════════════════════

OTP_TTL = 300        # OTP is valid for 5 minutes
VERIFIED_TTL = 600   # temp_token is valid for 10 minutes


def _norm_email(value):
    """Trim and lowercase an email address."""
    return (value or "").strip().lower()


def _norm_number(value):
    """Trim a phone number."""
    return (value or "").strip()


def get_point_settings():
    """Return the singleton PointSetting row, falling back to settings defaults."""
    setting = PointSetting.objects.first()
    if not setting:
        setting = PointSetting(
            registration_bonus_points=settings.REGISTRATION_BONUS,
            point_value=settings.POINT_VALUE,
        )
    return setting


def _find_user(number=None, email=None):
    """
    Look up an AppUser by email or phone number.
    Also handles the +92 / 0 phone format mismatch.
    """
    user = None

    if email:
        user = AppUser.objects.filter(email__iexact=email).first()

    if not user and number:
        user = AppUser.objects.filter(number=number).first()
        if not user and number.startswith("+92"):
            user = AppUser.objects.filter(number="0" + number[3:]).first()
        if not user and number.startswith("0"):
            user = AppUser.objects.filter(number="+92" + number[1:]).first()

    return user


def _send_email_otp(email, otp, purpose="register", name=""):
   
    title = "Verify your account" if purpose == "register" else "Reset your password"
    try:
        html = render_to_string("emails/otp_email.html", {
            "code": otp,
            "title": title,
            "name": name,
            "minutes": OTP_TTL // 60,
        })
        msg = EmailMultiAlternatives(
            subject=f"{title} - Code {otp}",
            body=f"Your OTP is {otp}. It expires in {OTP_TTL // 60} minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        return True, None
    except Exception as e:
        import traceback
        print("EMAIL OTP FAILED:", repr(e))
        traceback.print_exc()
        return False, str(e)


def _send_otp_both(number=None, email=None, prefix="otp", purpose="register", name=""):
   
    otp = str(random.randint(1000, 9999))
    sent = []
    errors = {}

    if number:
        try:
            send_sms(number, f"Your OTP is {otp}")
            sent.append("sms")
        except Exception as e:
            errors["sms"] = str(e)

    if email:
        ok, err = _send_email_otp(email, otp, purpose, name)
        if ok:
            sent.append("email")
        else:
            errors["email"] = err

    # Only cache the OTP if at least one channel succeeded
    if sent:
        if number:
            cache.set(f"{prefix}_{number}", otp, timeout=OTP_TTL)
        if email:
            cache.set(f"{prefix}_{email}", otp, timeout=OTP_TTL)

    return otp, sent, errors


# ═══════════════════════════════════════════════════════════════
# REGISTER STEP 1 : Send OTP to phone number and email
# ═══════════════════════════════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def create_app_user(request):
    number = _norm_number(request.data.get("number"))
    email = _norm_email(request.data.get("email"))

    if not number and not email:
        return Response({"error": "Either number or email is required"}, status=400)

    # Validate phone number
    if number:
        if not re.fullmatch(r"\+?\d{9,15}", number):
            return Response({"error": "Enter a valid phone number."}, status=400)
        if AppUser.objects.filter(number=number).exists():
            return Response({"error": "Number already registered"}, status=400)

    # Validate email address
    if email:
        try:
            validate_email(email)
        except DjangoValidationError:
            return Response({"error": "Enter a valid email address."}, status=400)
        if AppUser.objects.filter(email__iexact=email).exists():
            return Response({"error": "Email already registered"}, status=400)

    otp, sent, errors = _send_otp_both(
        number=number or None,
        email=email or None,
        prefix="otp",
        purpose="register",
    )

    if not sent:
        return Response({
            "error": "Failed to send OTP. Please try again.",
            "details": errors,
        }, status=500)

    return Response({
        "message": "OTP sent",
        "number": number,
        "email": email,
        "sent_to": sent,
        "failed": list(errors),
    }, status=200)


# ═══════════════════════════════════════════════════════════════
# REGISTER STEP 2 : Verify the OTP (by number or by email)
# ═══════════════════════════════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    number = _norm_number(request.data.get("number"))
    email = _norm_email(request.data.get("email"))
    otp = str(request.data.get("otp", "")).strip()

    if not number and not email:
        return Response({"error": "Either number or email is required"}, status=400)
    if not otp:
        return Response({"error": "OTP is required"}, status=400)

    # Check both cache keys — whichever one is present
    cached_otp = None
    if number:
        cached_otp = cache.get(f"otp_{number}")
    if cached_otp is None and email:
        cached_otp = cache.get(f"otp_{email}")

    if cached_otp is None:
        return Response({"error": "OTP expired"}, status=400)

    if cached_otp != otp:
        return Response({"error": "Invalid OTP"}, status=400)

    temp_token = secrets.token_urlsafe(32)

    # Store the token under both keys so step 3 works with either identifier
    if number:
        cache.set(f"verified_{number}", temp_token, timeout=VERIFIED_TTL)
        cache.delete(f"otp_{number}")
    if email:
        cache.set(f"verified_{email}", temp_token, timeout=VERIFIED_TTL)
        cache.delete(f"otp_{email}")

    return Response({
        "message": "OTP verified. Please complete your profile.",
        "temp_token": temp_token,
        "number": number,
        "email": email,
    }, status=200)


# ═══════════════════════════════════════════════════════════════
# REGISTER STEP 3 : Complete the profile — the user is created here
# ═══════════════════════════════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def complete_profile(request):
    number = _norm_number(request.data.get("number"))
    email = _norm_email(request.data.get("email"))
    temp_token = request.data.get("temp_token")
    name = (request.data.get("name") or "").strip()
    password = request.data.get("password") or ""
    confirm_password = request.data.get("confirm_password")

    if not number and not email:
        return Response({"error": "Either number or email is required"}, status=400)

    # Validate the token issued in step 2
    cached_token = None
    if number:
        cached_token = cache.get(f"verified_{number}")
    if not cached_token and email:
        cached_token = cache.get(f"verified_{email}")

    if not cached_token or cached_token != temp_token:
        return Response({"error": "Invalid or expired token"}, status=400)

    # Password checks
    if len(password) < 6:
        return Response({"error": "Password must be at least 6 characters"}, status=400)

    if confirm_password is not None and password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)

    # Guard against someone registering the same identifier meanwhile
    if number and AppUser.objects.filter(number=number).exists():
        return Response({"error": "Number already registered"}, status=400)

    if email and AppUser.objects.filter(email__iexact=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    points_to_add = get_point_settings().registration_bonus_points

    user = AppUser.objects.create(
        number=number or None,
        email=email or None,
        name=name,
        password_hash=make_password(password),
        is_verified=True,
        api_token=secrets.token_urlsafe(32),
        points=points_to_add,
    )

    if number:
        cache.delete(f"verified_{number}")
    if email:
        cache.delete(f"verified_{email}")

    return Response({
        "id": user.id,
        "number": user.number,
        "name": user.name,
        "email": user.email,
        "points": user.points,
        "api_token": user.api_token,
        "created_at": user.created_at,
    }, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════
# RESEND OTP (registration)
# ═══════════════════════════════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    number = _norm_number(request.data.get("number"))
    email = _norm_email(request.data.get("email"))

    if not number and not email:
        return Response({"error": "Either number or email is required"}, status=400)

    if number and AppUser.objects.filter(number=number).exists():
        return Response({"error": "Number already registered"}, status=400)

    if email and AppUser.objects.filter(email__iexact=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    otp, sent, errors = _send_otp_both(
        number=number or None,
        email=email or None,
        prefix="otp",
        purpose="register",
    )

    if not sent:
        return Response({"error": "Failed to send OTP.", "details": errors}, status=500)

    return Response({
        "message": "OTP resent",
        "sent_to": sent,
        "failed": list(errors),
    }, status=200)


# ═══════════════════════════════════════════════════════════════
# FORGOT PASSWORD STEP 1 : Send OTP to phone number and email
# ═══════════════════════════════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    number = _norm_number(request.data.get("number"))
    email = _norm_email(request.data.get("email"))

    if not number and not email:
        return Response({"error": "Either number or email is required"}, status=400)

    user = _find_user(number=number or None, email=email or None)
    if not user:
        return Response({"error": "User not found"}, status=404)

    # Send to the user's registered number and email, whichever exist
    otp, sent, errors = _send_otp_both(
        number=user.number or None,
        email=user.email or None,
        prefix="forgot_otp",
        purpose="forgot",
        name=user.name or "",
    )

    if not sent:
        return Response({
            "error": "Failed to send OTP. Please try again.",
            "details": errors,
        }, status=500)

    return Response({
        "message": "OTP sent",
        "number": user.number,
        "email": user.email,
        "sent_to": sent,
        "failed": list(errors),
    }, status=200)


# ═══════════════════════════════════════════════════════════════
# FORGOT PASSWORD STEP 2 : Verify OTP and set the new password
# ═══════════════════════════════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    number = _norm_number(request.data.get("number"))
    email = _norm_email(request.data.get("email"))
    otp = str(request.data.get("otp", "")).strip()
    new_password = request.data.get("new_password") or ""
    confirm_password = request.data.get("confirm_password")

    if not number and not email:
        return Response({"error": "Either number or email is required"}, status=400)

    if not otp or not new_password:
        return Response({"error": "otp and new_password are required"}, status=400)

    if len(new_password) < 6:
        return Response({"error": "Password must be at least 6 characters"}, status=400)

    if confirm_password is not None and new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)

    user = _find_user(number=number or None, email=email or None)
    if not user:
        return Response({"error": "User not found"}, status=404)

    # The OTP is cached under the user's registered number and email
    cached_otp = None
    if user.number:
        cached_otp = cache.get(f"forgot_otp_{user.number}")
    if cached_otp is None and user.email:
        cached_otp = cache.get(f"forgot_otp_{user.email}")

    if cached_otp is None:
        return Response({"error": "OTP expired"}, status=400)

    if cached_otp != otp:
        return Response({"error": "Invalid OTP"}, status=400)

    user.password_hash = make_password(new_password)
    user.api_token = secrets.token_urlsafe(32)   # invalidate old sessions
    user.save(update_fields=["password_hash", "api_token"])

    if user.number:
        cache.delete(f"forgot_otp_{user.number}")
    if user.email:
        cache.delete(f"forgot_otp_{user.email}")

    return Response({"message": "Password reset successfully"}, status=200)


# ═══════════════════════════════════════════════════════════════
# LOGIN — works with either the phone number or the email
# ═══════════════════════════════════════════════════════════════
@api_view(["POST"])
@permission_classes([AllowAny])
def app_user_login(request):
    number = _norm_number(request.data.get("number"))
    email = _norm_email(request.data.get("email"))
    password = request.data.get("password")

    if not password or (not number and not email):
        return Response({"detail": "Number/Email and password required"},
                        status=status.HTTP_400_BAD_REQUEST)

    user = _find_user(number=number or None, email=email or None)

    if not user or not check_password(password, user.password_hash):
        return Response({"detail": "Invalid credentials"},
                        status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({"detail": "Account is deactivated"},
                        status=status.HTTP_403_FORBIDDEN)

    if not user.api_token:
        user.api_token = secrets.token_urlsafe(32)
        user.save(update_fields=["api_token"])

    return Response({
        "id": user.id,
        "number": user.number,
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
        "api_token": user.api_token,
    }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════
# APP USER — remaining APIs
# ═══════════════════════════════════════════════════════════════
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

    addresses = request.data.get("addresses", [])

    # Accept a JSON string payload as well
    if isinstance(addresses, str):
        try:
            addresses = json.loads(addresses)
        except json.JSONDecodeError:
            return Response({"error": "Invalid address format"}, status=status.HTTP_400_BAD_REQUEST)

    # Wrap a single address object in a list
    if isinstance(addresses, dict):
        addresses = [addresses]

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


@api_view(["GET"])
def app_user_list(request):
    users = AppUser.objects.all().order_by("-created_at")
    serializer = AppUserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
def account_delete(request, pk):
    user = get_object_or_404(AppUser, pk=pk)
    user.delete()
    return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(["DELETE"])
def delete_user_address(request, pk):
    address = get_object_or_404(Address, pk=pk)
    address.delete()
    return Response({"message": "Address deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════
# CONTENT APIs
# ═══════════════════════════════════════════════════════════════
@api_view(['GET'])
def category_list_api(request):
    categories = Category.objects.all().order_by('-id')
    serializer = CategorySerializer(categories, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def brand_list_api(request):
    brands = Brand.objects.all().order_by('-id')
    serializer = BrandSerializer(brands, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def privacy_content_api(request):
    privacy = Privacy.objects.all().order_by('-id')
    serializer = PrivacySerializer(privacy, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def about_content_api(request):
    about = About.objects.all().order_by('-id')
    serializer = AboutSerializer(about, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def contact_content_api(request):
    contact = ContactInfo.objects.all().order_by('-id')
    serializer = ContactInfoSerializer(contact, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def banner_list_api(request):
    banners = Banner.objects.all().order_by('-id')
    serializer = BannerSerializer(banners, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def ad_list_api(request):
    ads = Ad.objects.all().order_by('-id')
    serializer = AdSerializer(ads, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def hero_list_api(request):
    heros = Hero.objects.all().order_by('-id')
    serializer = HeroSerializer(heros, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold', '-id')
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


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


@api_view(['GET'])
def active_discount_popup(request):
    popup = DiscountPopup.objects.filter(is_active=True).order_by('-created_at').first()

    if not popup:
        return Response({"message": "No active popup"})

    serializer = DiscountPopupSerializer(popup)
    return Response(serializer.data)


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


# ═══════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════
@api_view(["GET"])
def list_orders(request):
    orders = Order.objects.all().order_by("-created_at")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


def _validate_and_calculate_coupon(discount, user, items_data):
    """Validate a coupon against a cart and calculate the discount."""
    now = timezone.now()

    # 1. Active window check
    if not discount.active:
        return {"valid": False, "message": "Coupon is inactive."}
    if discount.start_date and discount.start_date > now:
        return {"valid": False, "message": "Coupon is not active yet."}
    if discount.end_date and discount.end_date < now:
        return {"valid": False, "message": "Coupon has expired."}

    # 2. Restricted to specific users
    if not discount.apply_all_users:
        if not user:
            return {"valid": False, "message": "Login required to use this coupon."}
        if not discount.users.filter(id=user.id).exists():
            return {"valid": False, "message": "This coupon is not valid for your account."}

    # 3. One-time use per user
    if user is not None and UsedCoupon.objects.filter(user=user, discount=discount).exists():
        return {"valid": False, "message": "You have already used this coupon."}

    # 4. Calculation and product eligibility
    discount_value = Decimal(str(discount.value))
    is_percent = discount.discount_type == Discount.PERCENTAGE
    discount_amount = Decimal("0.00")
    final_total = Decimal("0.00")
    applied_product_ids = []

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
        eligible_product_ids = set(discount.products.values_list('id', flat=True))
        eligible_items = []
        non_eligible_items = []

        for item in items_data:
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
    phone = request.data.get("phone")

    if not code:
        return Response({"valid": False, "message": "Coupon code is required."}, status=400)
    if not items:
        return Response({"valid": False, "message": "No items provided."}, status=400)

    try:
        discount = Discount.objects.get(code__iexact=code)
    except Discount.DoesNotExist:
        return Response({"valid": False, "message": "Invalid coupon code."}, status=404)

    user = None
    if user_id:
        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response({"valid": False, "message": "Invalid user."}, status=400)
    elif phone:
        try:
            user = AppUser.objects.get(number=phone)
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

            points_discount = Decimal("0.00")
            discount_obj = None
            discount_amount = Decimal("0.00")
            products_data = data.get("product", [])

            # ── Loyalty points ──
            if applied_points > 0:
                if applied_points > (app_user.points or 0):
                    return Response({
                        "error": f"Insufficient points. You have {app_user.points}, requested {applied_points}."
                    }, status=400)

                point_setting = get_point_settings()
                points_discount = Decimal(applied_points) * Decimal(point_setting.point_value)

                app_user.points = (app_user.points or 0) - applied_points
                app_user.save(update_fields=["points"])

            # ── Coupon validation ──
            if discount_code:
                try:
                    discount_obj = Discount.objects.get(code__iexact=discount_code)

                    items_for_validation = []
                    for item in products_data:
                        item_id = item.get("id") or item.get("product_id")

                        # Normalise the id to an int
                        try:
                            item_id = int(item_id) if item_id is not None else None
                        except (ValueError, TypeError):
                            item_id = None

                        # Fall back to looking the product up by name
                        if not item_id and item.get("name"):
                            product = Product.objects.filter(name=item.get("name")).first()
                            if product:
                                item_id = product.id

                        items_for_validation.append({
                            "id": item_id,
                            "price": item.get("price", 0),
                            "quantity": item.get("quantity", 1),
                        })

                    validation = _validate_and_calculate_coupon(
                        discount_obj, app_user, items_for_validation
                    )

                    if not validation["valid"]:
                        return Response({"error": validation["message"]}, status=400)

                    discount_amount = validation["discount_amount"]

                except Discount.DoesNotExist:
                    return Response({"error": "Invalid coupon code."}, status=400)

            # ── Create the order ──
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

            # ── Create the order items ──
            total = Decimal("0.00")

            for item in products_data:
                # Image can be a base64 data URI, a remote URL, or an uploaded file
                image_data = item.get("image")
                image_file = None
                if isinstance(image_data, dict):
                    image_data = image_data.get("uri")

                if image_data and isinstance(image_data, str):
                    if image_data.startswith("data:image"):
                        try:
                            img_format, imgstr = image_data.split(";base64,")
                            ext = img_format.split("/")[-1]
                            image_file = ContentFile(base64.b64decode(imgstr), name=f"order_item.{ext}")
                        except Exception:
                            pass
                    elif image_data.startswith("http"):
                        try:
                            resp = requests.get(image_data, timeout=5)
                            if resp.status_code == 200:
                                ext = image_data.split(".")[-1].split("?")[0]
                                image_file = ContentFile(resp.content, name=f"order_item.{ext}")
                        except Exception:
                            pass
                elif image_data and not isinstance(image_data, str):
                    image_file = image_data

                price = Decimal(str(item.get("price", 0)))
                qty = int(item.get("quantity", 1))
                total += price * qty

                product_id = item.get("id") or item.get("product_id")
                try:
                    product_id = int(product_id) if product_id is not None else None
                except (ValueError, TypeError):
                    product_id = None

                if not product_id and item.get("name"):
                    product = Product.objects.filter(name=item.get("name")).first()
                    if product:
                        product_id = product.id

                OrderItem.objects.create(
                    order=order,
                    product_id=product_id,
                    image=image_file,
                    name=item.get("name"),
                    pts=(item.get("pts", 0) or 0) * qty,
                    variants=item.get("variants", ""),
                    price=price,
                    cost_price=item.get("cost_price", 0),
                    quantity=qty,
                )

            # ── Final total ──
            final_total = total - discount_amount - points_discount
            if final_total < 0:
                final_total = Decimal("0.00")

            order.total_amount = final_total
            order.save(update_fields=["total_amount"])

            # ── Record the coupon usage ──
            if discount_obj:
                UsedCoupon.objects.create(
                    user=app_user,
                    discount=discount_obj,
                    order=order
                )
                Discount.objects.filter(id=discount_obj.id).update(used_count=F('used_count') + 1)

            # ── Payment records ──
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
                    # Redeem orders do not earn points
                    pass
                else:
                    # Normal order — award the earned points
                    earned = order.items.aggregate(total=Sum("pts"))["total"] or 0
                    if earned > 0:
                        AppUser.objects.filter(pk=order.user.pk).update(
                            points=F("points") + earned
                        )

                    # First delivered order bonus
                    first_order = not Order.objects.filter(
                        user=order.user,
                        status="delivered"
                    ).exclude(pk=order.pk).exists()

                    if first_order:
                        AppUser.objects.filter(pk=order.user.pk).update(
                            points=F("points") + 20
                        )

            Order.objects.filter(id=order_pk).update(
                status=new_status,
                is_points_added=True
            )
        else:
            Order.objects.filter(id=order_pk).update(status=new_status)

    order.refresh_from_db()

    return Response({
        "message": "Status updated",
        "order": OrderSerializer(order).data
    })


# ═══════════════════════════════════════════════════════════════
# VIEWSETS
# ═══════════════════════════════════════════════════════════════
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all().order_by('position')
    serializer_class = ProductSerializer


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by('position')
    serializer_class = CategorySerializer


class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all().order_by('position')
    serializer_class = BrandSerializer


# ═══════════════════════════════════════════════════════════════
# RIDER APIs
# ═══════════════════════════════════════════════════════════════
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

        # Support both hashed and legacy plain-text passwords
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


@api_view(["POST"])
@permission_classes([AllowAny])
def rider_forgot_password_api(request):
    email = request.data.get("email", "").strip()

    if not email:
        return Response({"error": "Email is required."}, status=400)

    try:
        rider = Rider.objects.get(email__iexact=email)

        # Drop any previous tokens and issue a fresh one
        RiderPasswordResetToken.objects.filter(rider=rider).delete()
        token_obj = RiderPasswordResetToken.objects.create(rider=rider)

        reset_link = request.build_absolute_uri(
            f"/rider/reset-password/{token_obj.token}/"
        )

        send_mail(
            subject="Password Reset Request",
            message=f"Hi {rider.name},\n\nYour password reset link:\n{reset_link}\n\nThis link will expire in 1 hour.\n\nIf you did not request this, ignore this email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[rider.email],
            fail_silently=False,
        )

        return Response({"message": "Reset link sent to your email."}, status=200)

    except Rider.DoesNotExist:
        return Response({"error": "No rider found with this email."}, status=404)


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


@api_view(["GET"])
@permission_classes([AllowAny])
def rider_orders_api(request, rider_id):
    """Orders assigned to a rider."""
    try:
        rider = Rider.objects.get(id=rider_id)
    except Rider.DoesNotExist:
        return Response({"error": "Rider not found."}, status=404)

    orders = Order.objects.filter(rider=rider).order_by("-id")

    return Response({
        "rider": RiderSerializer(rider).data,
        "orders": RiderOrderSerializer(orders, many=True).data
    }, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
def rider_update_order_status_api(request, order_id):
    rider_id = request.data.get("rider_id")
    new_status = request.data.get("status", "").strip()
    cancel_reason = request.data.get("cancel_reason", "").strip()

    ALLOWED_STATUSES = ["pending", "on_the_way", "delivered", "cancelled"]

    if not rider_id:
        return Response({"error": "rider_id required."}, status=400)

    if new_status not in ALLOWED_STATUSES:
        return Response({
            "error": f"Invalid status. Allowed: {', '.join(ALLOWED_STATUSES)}"
        }, status=400)

    if new_status == "cancelled" and not cancel_reason:
        return Response({"error": "Please provide a reason for cancellation."}, status=400)

    try:
        order = Order.objects.get(id=order_id, rider_id=rider_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or not assigned to you."}, status=404)

    if order.status in ["delivered", "cancelled"]:
        return Response({
            "error": f"Order is already {order.status}. No further changes allowed."
        }, status=400)

    if not Rider.objects.filter(id=rider_id).exists():
        return Response({"error": "Rider not found."}, status=404)

    order.status = new_status

    if new_status == "cancelled":
        order.cancel_reason = cancel_reason

    if new_status == "delivered" and not order.is_points_added:
        if order.user and order.type != "redeem":
            earned = order.items.aggregate(total=Sum("pts"))["total"] or 0
            if earned > 0:
                AppUser.objects.filter(pk=order.user.pk).update(
                    points=F("points") + earned
                )

            # First delivered order bonus
            first_order = not Order.objects.filter(
                user=order.user,
                status="delivered"
            ).exclude(pk=order.pk).exists()

            if first_order:
                AppUser.objects.filter(pk=order.user.pk).update(
                    points=F("points") + 20
                )

        order.is_points_added = True

    order.save()

    return Response({
        "message": "Order status updated successfully.",
        "order_id": order.id,
        "status": order.status,
        "cancel_reason": order.cancel_reason if new_status == "cancelled" else None,
    }, status=200)
