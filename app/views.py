from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from twilio.rest import Client
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.conf import settings
from collections import defaultdict
from django.db import IntegrityError, transaction
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .reports import get_sales_report, get_profit_report, get_customer_potentials, get_product_report, get_product_profit_report
from .forms import CategoryForm, RiderForm, BrandForm, BannerForm, ProductForm, RedeemForm, AdForm, HeroForm, PrivacyForm, DiscountForm, AboutForm, ContactInfoForm
from .models import Product, PointSetting, VariantOption, VariantValue, Redeem, ProductVariant, City, Rider, Category, Brand, ProductImage, Banner, Ad, Hero, Order, OrderItem, Payment, Review, AppUser, Address, Privacy, About, ContactInfo, ContactForm, Discount

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

@login_required(login_url='login')
def reports(request):
    context = {
        "sales": get_sales_report(),
        "profit": get_profit_report(),
        "top_customers": get_customer_potentials(),
        "products": get_product_report(),
        "product_profit" : get_product_profit_report(),

    }
    return render(request, "pages/reports.html", context)

@login_required(login_url='login')
def dashboard(request):
    total_users = AppUser.objects.count()
    total_orders = Order.objects.filter(status="delivered").count()
    total_sales = (
    OrderItem.objects
    .filter(order__status="delivered")
    .aggregate(total=Sum('price'))['total'] or 0
)
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]

    # Total sale (sum of all OrderItem.price * quantity)
    total_amount = (
        OrderItem.objects.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
    )

    # Pending stats
    pending_orders_qs = Order.objects.filter(status='pending')
    pending_orders_count = pending_orders_qs.count()
    pending_amount = (
        OrderItem.objects.filter(order__status='pending')
        .aggregate(total=Sum(F('price')))['total'] or 0
    )

    # Delivered stats
    delivered_orders = Order.objects.filter(status='delivered').count()
    delivered_amount = (
        OrderItem.objects.filter(order__status='delivered')
        .aggregate(total=Sum(F('price')))['total'] or 0
    )

    # Canceled stats
    canceled_orders = Order.objects.filter(status='cancelled').count()
    canceled_amount = (
        OrderItem.objects.filter(order__status='cancelled')
        .aggregate(total=Sum(F('price')))['total'] or 0
    )

    # Monthly chart data
    monthly_data = (
        Order.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total_orders=Count('id'))
        .order_by('month')
    )

    monthly_sales = (
        OrderItem.objects.annotate(month=TruncMonth('order__created_at'))
        .values('month')
        .annotate(total_sales=Sum(F('price') * F('quantity')))
        .order_by('month')
    )

    # Merge both datasets
    labels = [m['month'].strftime("%b %Y") for m in monthly_data]
    order_counts = [m['total_orders'] for m in monthly_data]
    sales_lookup = {s['month']: s['total_sales'] for s in monthly_sales}
    sales_data = [float(sales_lookup.get(m['month'], 0)) for m in monthly_data]

    # Prepare notification data
    notifications = []
    for order in pending_orders_qs.select_related('user').prefetch_related('items').order_by('-created_at')[:10]:
        total_amt = (
            order.items.aggregate(total=Sum(F("price")))["total"] or 0
        )
        notifications.append({
            "id": order.id,
            "user_number": order.user.number if order.user else "Guest",
            "status": order.status,
            "total": float(total_amt),
            "created_at": order.created_at.strftime("%b %d, %Y %H:%M"),
        })

    context = {
        "notifications": notifications,
        "new_notifications": len(notifications),
        'total_orders': total_orders,
        'total_users': total_users,
        'total_sales': total_sales,
        'recent_orders': recent_orders,
        'total_amount': total_amount,
        'pending_orders_count': pending_orders_count,
        'pending_amount': pending_amount,
        'delivered_orders': delivered_orders,
        'delivered_amount': delivered_amount,
        'canceled_orders': canceled_orders,
        'canceled_amount': canceled_amount,
        'labels': labels,
        'order_counts': order_counts,
        'sales_data': sales_data,
    }
    return render(request, 'pages/main.html', context)


def mark_notifications_read(request):
    if request.method == "POST":
        Order.objects.filter(status='pending', is_read=False).update(is_read=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

@csrf_exempt  
def clear_notifications(request):
    if request.method == "POST":
        if hasattr(Order, 'is_read'):
            Order.objects.filter(status="pending", is_read=False).update(is_read=True)
        else:
            pass
        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False}, status=400)



# views.py
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from app.models import RiderPasswordResetToken  # apna app name

# ----------------------------
# STEP 1: Forget Password Page
# ----------------------------
def rider_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

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

            # Email bhejo
            send_mail(
                subject="Password Reset Request",
                message=f"Hi {rider.name},\n\nYour password reset link:\n{reset_link}\n\nThis link will expire in 1 hour.\n\nIf you did not request this, ignore this email.",
                from_email=None,  # settings.py wala use hoga
                recipient_list=[rider.email],
                fail_silently=False,
            )

            messages.success(request, "Reset link sent to your email!")
            return redirect("rider_forgot_password")

        except Rider.DoesNotExist:
            messages.error(request, "No rider found with this email")
            return redirect("rider_forgot_password")

    return render(request, "rider_forgot_password.html")


# ----------------------------
# STEP 2: Reset Password Page
# ----------------------------
def rider_reset_password(request, token):
    try:
        token_obj = RiderPasswordResetToken.objects.get(token=token)
    except RiderPasswordResetToken.DoesNotExist:
        messages.error(request, "Invalid reset link")
        return redirect("login")

    if not token_obj.is_valid():
        messages.error(request, "Reset link expired. Please request again.")
        return redirect("rider_forgot_password")

    if request.method == "POST":
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "rider_reset_password.html", {"token": token})

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters")
            return render(request, "rider_reset_password.html", {"token": token})

        # Password update karo
        rider = token_obj.rider
        rider.password = make_password(password)
        rider.save()

        # Token use ho gaya
        token_obj.is_used = True
        token_obj.save()

        messages.success(request, "Password reset successful! Please login.")
        return redirect("login")

    return render(request, "rider_reset_password.html", {"token": token})          



# Dashborad Admin Panel User Login
def user_login(request):

    username = ""
    password = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        # ----------------------
        # ADMIN LOGIN
        # ----------------------
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, "Admin account is inactive")
                return redirect("login")

            login(request, user)
            request.session["is_rider"] = False
            messages.success(request, "Admin login successful")
            return redirect("dashboard")

        # ----------------------
        # RIDER LOGIN
        # ----------------------
        try:
            rider = Rider.objects.get(email__iexact=username)

            # ❌ BLOCK inactive rider
            if not rider.is_active:
                messages.error(request, "Your account is inactive")
                return redirect("login")

            if rider.password.startswith("pbkdf2"):
                login_success = check_password(password, rider.password)
            else:
                login_success = (password == rider.password)

            if login_success:
                request.session["rider_id"] = rider.id
                request.session["is_rider"] = True
                messages.success(request, f"Welcome {rider.name}")
                return redirect("order_list_ui")
            else:
                messages.error(request, "Wrong password")
                return redirect("login")

        except Rider.DoesNotExist:
            messages.error(request, "Rider not found")
            return redirect("login")

    return render(request, "login.html")


# Dashborad Admin Panel User Logout
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out")
    return redirect("login")

#  Home → Login redirect
def home(request):
    return redirect('login')


# Dashboard App User List
def appuser_list_ui(request):
    users = AppUser.objects.all().order_by("-created_at")
    return render(request, "pages/customer-list.html", {"users": users})


# Active & Deactive 
def user_status(request, pk):
    user = get_object_or_404(AppUser, pk=pk)
    user.is_active = not user.is_active  
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.number} has been {status}.")
    
    return redirect('appuser_list') 


# Dashboard App User Creation
@login_required(login_url='login')
def create_appuser_ui(request, pk=None):
    if pk:
        user = get_object_or_404(AppUser, pk=pk)
        success_message = "User updated successfully"
    else:
        user = None
        success_message = "User created successfully"

    if request.method == "POST":
        number = request.POST.get("number")
        name = request.POST.get("name")
        email = request.POST.get("email")
        image = request.FILES.get("image")  
        password = request.POST.get("password")

        # Check for duplicate number (ignore if updating same user)
        if AppUser.objects.filter(number=number).exclude(pk=pk).exists():
            messages.error(request, "User already exists with this number!")
            return redirect("create_appuser")

        # Create or update user
        if user:
            user.number = number
            user.name = name
            user.email = email
            if image:
                user.image = image
            if password:
                user.password_hash = make_password(password)
            user.save()
        else:
            AppUser.objects.create(
                number=number,
                name=name,
                email=email,
                image=image,
                password_hash=make_password(password),
                api_token=get_random_string(40)
            )
        
        messages.success(request, success_message)
        return redirect("appuser_list")

    return render(request, "pages/create-user.html", {"user": user})


def customer_address(request, pk):
    user = get_object_or_404(AppUser, pk=pk)
    
    if request.method == "POST":
        # Collect form data
        address_data = {
            "street": request.POST.get("address[street]", "").strip(),
            "city": request.POST.get("address[city]", "").strip(),
            "state": request.POST.get("address[state]", "").strip(),
            "postal_code": request.POST.get("address[postal_code]", "").strip(),
            "country": request.POST.get("address[country]", "").strip(),
        }

        #  Check if at least one field is filled
        if any(address_data.values()):
            Address.objects.create(user=user, **address_data)
            messages.success(request, "Address added successfully")
            return redirect("customer_detail", pk=user.pk)
        else:
            messages.error(request, "Please fill at least one address field")

    return render(request, "pages/customer_detail.html", {"user": user})


def customer_address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk)
    user = address.user
    address.delete()
    messages.warning(request, "Address deleted successfully!")
    return redirect("customer_detail" , pk=user.pk)

# Dashboard App User Delete
@login_required(login_url='login')
def delete_appuser_ui(request, pk):
    user = get_object_or_404(AppUser, pk=pk)
    user.delete()
    messages.warning(request, "User deleted successfully!")
    return redirect('appuser_list')


# Admin App Customer Details
# def customer_detail(request, pk):
#     user = get_object_or_404(AppUser, pk=pk)

#     # Details orders
#     addresses = Address.objects.filter(user=user)
#     orders = Order.objects.filter(status="delivered", user=user)
#     normal_orders = orders.filter(type="normal")
#     redeem_orders = orders.filter(type="redeem")

#     normal_orders_data = []
#     redeem_orders_data = []

#     # Normal orders
#     for order in normal_orders:
#         items = order.items.all()
#         order_points = sum(item.pts for item in items)
#         normal_orders_data.append({
#             "order": order,
#             "items": items,
#             "order_points": order_points,
#         })

#     # Redeem orders
#     for order in redeem_orders:
#         items = order.items.all()
#         order_points = sum(item.pts for item in items)
#         redeem_orders_data.append({
#             "order": order,
#             "items": items,
#             "order_points": order_points,
#         })

#     # Calculate points
#     earned_points = sum(i["order_points"] for i in normal_orders_data)
#     spent_points = sum(i["order_points"] for i in redeem_orders_data)
#     available_points = earned_points - spent_points

#     context = {
#         "user": user,
#         "normal_orders_data": normal_orders_data,
#         "redeem_orders_data": redeem_orders_data,
#         "normal_orders": normal_orders,
#         "redeem_orders": redeem_orders,
#         "earned_points": earned_points,
#         "spent_points": spent_points,
#         "available_points": available_points,
#         "addresses": addresses  
#     }

#     return render(request, "pages/customer_detail.html", context)




def customer_detail(request, pk):
    user = get_object_or_404(AppUser, pk=pk)

    point_setting = PointSetting.objects.first()
    point_value = point_setting.point_value if point_setting else 0.50

    addresses = Address.objects.filter(user=user)
    orders = Order.objects.filter(user=user, status="delivered").order_by('-created_at')

    normal_orders_data = []
    redeem_orders_data = []

    earned_points = 0
    spent_points = 0

    for order in orders:
        items = order.items.all()
        order_earned = sum(item.pts for item in items)
        order_spent = order.points_used or 0

        order_total = sum(item.price * item.quantity for item in items)
        cash_paid = order_total - (order.points_discount or 0)

        earned_points += order_earned
        spent_points += order_spent

        data = {
            "order": order,
            "items": items,
            "earned": order_earned,
            "spent": order_spent,
            "earned_rs": order_earned * point_value,
            "spent_rs": order_spent * point_value,
            "cash_paid": cash_paid,       
            "order_total": order_total,
        }

        # Redeem order = sirf points se buy, Normal = cash/mixed
        if order.type == "redeem":
            redeem_orders_data.append(data)
        else:
            normal_orders_data.append(data)

    available_points = user.points or 0

    context = {
        "user": user,
        "addresses": addresses,
        "normal_orders_data": normal_orders_data,
        "redeem_orders_data": redeem_orders_data,
        "earned_points": earned_points,
        "spent_points": spent_points,
        "available_points": available_points,
        "earned_rs": earned_points * point_value,
        "spent_rs": spent_points * point_value,
        "available_rs": available_points * point_value,
        "point_value": point_value,
    }

    return render(request, "pages/customer_detail.html", context)







# Add or Edit Category
@login_required(login_url='login')
def add_or_edit_category(request, pk=None):
    if pk:
        category = get_object_or_404(Category, pk=pk)
        success_message = "Category updated successfully"
    else:
        category = None
        success_message = "Category created successfully"

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("category")
        else:
            messages.error(request, "Something went wrong, please try again")
    else:
        form = CategoryForm(instance=category)

    return render(request, "pages/add-category.html", {"form": form, "category": category})


#  Category list with search
@login_required(login_url='login')
def category(request):
    search_query = request.GET.get('q', '')
    if search_query:
        categories = Category.objects.filter(name__icontains=search_query).order_by('-id')
    else:
        categories = Category.objects.all().order_by('-id')

    return render(request, "pages/category.html", {"categories": categories})


#  Delete Category
@login_required(login_url='login')
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.warning(request, "Category deleted successfully!")
    return redirect('category')


# Brand View
@login_required(login_url='login')
def add_or_edit_brand(request, pk=None):
    if pk:
        brand = get_object_or_404(Brand, pk=pk)
        success_message = "Brand updated successfully"
    else:
        brand = None
        success_message = "Brand created successfully"

    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("brand")
        else:
            messages.error(request, "Something went wrong, please try again")
    else:
        form = BrandForm(instance=brand)

    return render(request, "pages/add-brand.html", {"form": form, "brand": brand})




#  Brand list with search
@login_required(login_url='login')
def brand(request):
    search_query = request.GET.get('q', '')
    if search_query: 
        brands = Brand.objects.filter(name__icontains=search_query).order_by('-id')
    else:  
        brands = Brand.objects.all().order_by('-id')

    return render(request, "pages/brand.html", {"brands": brands})


# Delete Category
@login_required(login_url='login')
def delete_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.delete()
    messages.warning(request, "Brand deleted successfully!")
    return redirect('brand') 



# Privacy View
@login_required(login_url='login')
def add_or_edit_privacy(request, pk=None):
    if pk:
        privacy = get_object_or_404(Privacy, pk=pk)
        success_message = "Privacy updated successfully"
    else:
        privacy = None
        success_message = "Privacy created successfully"

    if request.method == "POST":
        form = PrivacyForm(request.POST, request.FILES, instance=privacy)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("privacy")
        else:
            messages.error(request, "Something went wrong, please try again")
    else:
        form = PrivacyForm(instance=privacy)

    return render(request, "pages/add-privacy.html", {"form": form, "privacy": privacy})



#  Brand list with search
@login_required(login_url='login')
def privacy(request):
    search_query = request.GET.get('q', '')
    if search_query: 
        privacies = Privacy.objects.filter(name__icontains=search_query).order_by('-id')
    else:  
        privacies = Privacy.objects.all().order_by('-id')
    return render(request, "pages/privacy.html", {"privacies": privacies})



# Delete Privacy
@login_required(login_url='login')
def delete_privacy(request, pk):
    privacy = get_object_or_404(Privacy, pk=pk)
    privacy.delete()
    messages.warning(request, "Privacy deleted successfully!")
    return redirect('privacy') 




# About View
@login_required(login_url='login')
def add_or_edit_about(request, pk=None):
    if pk:
        about = get_object_or_404(About, pk=pk)
        success_message = "About updated successfully"
    else:
        about = None 
        success_message = "About created successfully"

    if request.method == "POST":
        form = AboutForm(request.POST, request.FILES, instance=about)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("about")
        else:
            messages.error(request, "Something went wrong, please try again")
    else:
        form = AboutForm(instance=about)

    return render(request, "pages/add-about.html", {"form": form, "about": about })



#  About list with search
@login_required(login_url='login')
def about(request):
    search_query = request.GET.get('q', '')
    if search_query: 
        abouts = About.objects.filter(name__icontains=search_query).order_by('-id')
    else:  
        abouts = About.objects.all().order_by('-id')
    return render(request, "pages/about.html", {"abouts": abouts})



# Delete About
@login_required(login_url='login')
def delete_about(request, pk):
    about = get_object_or_404(About, pk=pk)
    about.delete()
    messages.warning(request, "About deleted successfully!")
    return redirect('about') 


# Contact View
@login_required(login_url='login')
def add_or_edit_contact(request, pk=None):
    if pk:
        contact = get_object_or_404(ContactInfo, pk=pk)
        success_message = "Contact Info updated successfully"
    else:
        contact = None 
        success_message = "Contact Info created successfully"

    if request.method == "POST":
        form = ContactInfoForm(request.POST, request.FILES, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("about")
        else:
            messages.error(request, "Something went wrong, please try again")
            print("Form Errors:", form.errors)
    else:
        form = ContactInfoForm(instance=contact)

    return render(request, "pages/add-contact.html", {"form": form, "contact": contact })



#  Contact list with search
@login_required(login_url='login')
def contact(request):
    search_query = request.GET.get('q', '')
    if search_query: 
        contacts = ContactInfo.objects.filter(name__icontains=search_query).order_by('-id')
    else:  
        contacts = ContactInfo.objects.all().order_by('-id')
    return render(request, "pages/contact.html", {"contacts": contacts})


#  Contact list with search
@login_required(login_url='login')
def contactform_list(request):
    search_query = request.GET.get('q', '')
    if search_query: 
        contactforms = ContactForm.objects.filter(name__icontains=search_query).order_by('-id')
    else:  
        contactforms = ContactForm.objects.all().order_by('-id')
    return render(request, "pages/contactform.html", {"contactforms": contactforms})

@login_required(login_url='login')
def get_contact_form(request, pk):
    try:
        contact = ContactForm.objects.get(pk=pk)
        data = {
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "phone": contact.phone,
            "message": contact.message
        }
        return JsonResponse(data)
    except ContactForm.DoesNotExist:
        return JsonResponse({"error": "Contact not found"}, status=404)

# Delete About
@login_required(login_url='login')
def delete_contact(request, pk):
    contact = get_object_or_404(ContactInfo, pk=pk)
    contact.delete()
    messages.warning(request, "Contact deleted successfully!")
    return redirect('contact') 

@login_required(login_url='login')
def delete_contactform(request, pk):
    contactform = get_object_or_404(ContactForm, pk=pk)
    contactform.delete()
    messages.warning(request, "Contact deleted successfully!")
    return redirect('contact_form')

# List Orders UI
def order_list_ui(request):
    is_rider = request.session.get("is_rider", False)
    rider_id = request.session.get("rider_id")

    if is_rider and rider_id:
        # Rider sirf apne assigned orders dekhe
        normal_orders = Order.objects.filter(type="normal", rider_id=rider_id).order_by("-created_at")
        redeem_orders = Order.objects.filter(type="redeem", rider_id=rider_id).order_by("-created_at")
    else:
        # Admin sab dekhe
        normal_orders = Order.objects.filter(type="normal").order_by("-created_at")
        redeem_orders = Order.objects.filter(type="redeem").order_by("-created_at")

    return render(request, "pages/order_list.html", {
        "normal_orders": normal_orders,
        "redeem_orders": redeem_orders,
    })


# Review 
# def reviews(request):
#     # Get all reviews with related user and product
#     reviews_qs = Review.objects.select_related('user', 'item').all()

#     # Calculate total spent per user dynamically
#     user_spent = (
#         Order.objects.filter(status="delivered")
#         .values('user_id')
#         .annotate(total_spent=Sum(ExpressionWrapper(F('items__price'), output_field=DecimalField())))
#     )
#     # Convert to dict for quick lookup
#     spent_dict = {item['user_id']: item['total_spent'] for item in user_spent}

#     # Attach total_spent to each review object
#     for review in reviews_qs:
#         review.total_spent = spent_dict.get(review.user.id, 0)

#     context = {
#         "reviews": reviews_qs,
#         "total_reviews": reviews_qs.count(),
#         "avg_rating": reviews_qs.aggregate(avg=Avg('rating'))["avg"] or 0,
#         "ratings": {
#             "five": reviews_qs.filter(rating=5).count(),
#             "four": reviews_qs.filter(rating=4).count(),
#             "three": reviews_qs.filter(rating=3).count(),
#             "two": reviews_qs.filter(rating=2).count(),
#             "one": reviews_qs.filter(rating=1).count(),
#         }
#     }
#     return render(request, "pages/reviews.html", context)


def reviews(request):
    reviews_qs = Review.objects.select_related('user', 'item').all().order_by('-created_at')
    user_spent = (
        Order.objects.filter(status="delivered")
        .values('user_id')
        .annotate(
            total_spent=Sum(
                ExpressionWrapper(F('items__price') * F('items__quantity'), output_field=DecimalField())
            )
        )
    )
    spent_dict = {item['user_id']: item['total_spent'] for item in user_spent}
    for review in reviews_qs:
        review.total_spent = spent_dict.get(review.user.id, 0) if review.user else 0

    # Aggregate ratings (only consider reviews with a user)
    ratings = {
        5: reviews_qs.filter(user__isnull=False, rating=5).count(),
        4: reviews_qs.filter(user__isnull=False, rating=4).count(),
        3: reviews_qs.filter(user__isnull=False, rating=3).count(),
        2: reviews_qs.filter(user__isnull=False, rating=2).count(),
        1: reviews_qs.filter(user__isnull=False, rating=1).count(),
    }

    # Sort ratings descending by star
    ratings_sorted = dict(sorted(ratings.items(), reverse=True))
    max_count = max(ratings.values())
    
    context = {
        "reviews": reviews_qs,
        "total_reviews": reviews_qs.filter(user__isnull=False).count(),
        "avg_rating": reviews_qs.filter(user__isnull=False).aggregate(avg=Avg('rating'))["avg"] or 0,
        "ratings": ratings_sorted,
        "max_count": max_count
    }

    return render(request, "pages/reviews.html", context)



@login_required(login_url='login')
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.warning(request, "Review deleted successfully!")
    return redirect('review')


# Create Order UI 
def create_order_ui(request):
    users = AppUser.objects.all() 
    if request.method == "POST":
        user_id = request.POST.get("user")
        address = request.POST.get("address")
        shipping = request.POST.get("shipping")
        status = request.POST.get("status", "pending")

        # Create order
        order = Order.objects.create(
            user_id=user_id,
            address=address,
            shipping=shipping,
            status=status
        )

        # Parse Order Items
        items = {}
        for key, value in request.POST.items():
            if key.startswith("items"):
                parts = key.replace("items[", "").replace("]", "").split("[")
                index, field = int(parts[0]), parts[1]
                if index not in items:
                    items[index] = {}
                items[index][field] = value

        # Save items
        for idx, item in items.items():   
            if item.get("name"):  
                image = request.FILES.get(f"items[{idx}][image]")  
                OrderItem.objects.create(
                    order=order,
                    image=image,
                    name=item.get("name"),
                    pts=item.get("pts") or 0,
                    variants=item.get("variants") or "",
                    price=item.get("price") or 0
                )

        return redirect("order_list_ui")

    return render(request, "pages/create_order.html", {"users": users})


def update_order_status_ui(request, pk):
    order = get_object_or_404(Order, pk=pk)
    cities = City.objects.all()

    # City from address
    order_city_name = get_city_from_address(order.address)
    order_city_id = None

    if order.city:
        order_city_name = order.city.name
        order_city_id = order.city.id
    elif order_city_name:
        try:
            city_obj = City.objects.get(name__iexact=order_city_name)
            order.city = city_obj
            order.save(update_fields=["city"])
            order_city_id = city_obj.id
        except City.DoesNotExist:
            pass

    if request.method == "POST":
        new_status = request.POST.get("status")
        city_id = request.POST.get("city")
        rider_id = request.POST.get("rider")

        if new_status:
            order.status = new_status

        if city_id:
            try:
                city_obj = City.objects.get(id=city_id)
                order.city = city_obj
            except City.DoesNotExist:
                pass

        if rider_id:
            try:
                rider = Rider.objects.get(id=rider_id)

                print(f"Order City: {order.city}")
                print(f"Rider Cities: {list(rider.cities.all())}")

                if order.city and order.city in rider.cities.all():
                    order.rider = rider
                    order.status = "on_the_way"
                else:
                    messages.error(request, "Rider not available in this city")
                    return redirect("update_order_status_ui", pk=pk)
            except Rider.DoesNotExist:
                pass

        order.save()
        messages.success(request, "Order updated successfully")
        return redirect("order_list_ui")

    return render(request, "pages/update_order.html", {
        "order": order,
        "cities": cities,
        "order_city_name": order_city_name,
        "order_city_id": order_city_id,
    })


import ast
import json

def get_city_from_address(address):
    if not address:
        return ""
    
    # Already dict hai
    if isinstance(address, dict):
        return address.get("city", "")
    
    if isinstance(address, str):
        # Try ast.literal_eval - single quote wale strings ke liye
        try:
            data = ast.literal_eval(address)
            return data.get("city", "")
        except:
            pass
        
        # Try json.loads - double quote wale strings ke liye
        try:
            data = json.loads(address)
            return data.get("city", "")
        except:
            pass
    
    return ""


# def update_order_status_ui(request, pk):
#     order = get_object_or_404(Order, pk=pk)

#     if request.method == "POST":
#         new_status = request.POST.get("status")
#         order.status = new_status
#         order.save()
#         return redirect("order_list_ui")

#     return render(request, "pages/update_order.html", {"order": order})

@login_required(login_url='login')
def delete_order_ui(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.warning(request, "Order deleted successfully!")
    return redirect('order_list_ui')



import json
from itertools import product as itertools_product
from collections import defaultdict
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Product, ProductImage, VariantOption, VariantValue, ProductVariant
from .forms import ProductForm



def _parse_variants_from_post(request):
    """
    Parse variants[N][field] = value  from POST / FILES.
    Returns list of dicts ordered by index.
    """
    variants = defaultdict(dict)

    for key, value in request.POST.items():
        if not key.startswith("variants["):
            continue
        try:
            idx   = key.split("[")[1].split("]")[0]
            field = key.split("[")[2].split("]")[0]
            variants[idx][field] = value
        except (IndexError, ValueError):
            pass

    for key, file in request.FILES.items():
        if not key.startswith("variants["):
            continue
        try:
            idx   = key.split("[")[1].split("]")[0]
            field = key.split("[")[2].split("]")[0]
            variants[idx][field] = file
        except (IndexError, ValueError):
            pass

    # Sort by numeric index so order is stable
    return [variants[k] for k in sorted(variants.keys(), key=lambda x: int(x))]


def _handle_product_variants(product_obj, request, is_edit=False):
    """
    Full variant pipeline:
      1. Parse options from opt_name[] / opt_values[]
      2. Save VariantOption + VariantValue
      3. Parse submitted variant rows
      4. Save / update ProductVariant rows
    """

    # ── 1. CLEAR OLD (edit mode) ──────────────────────────────────────────
    if is_edit:
        product_obj.variants.all().delete()
        product_obj.variant_options.all().delete()

    # ── 2. PARSE & SAVE OPTIONS ───────────────────────────────────────────
    opt_names  = request.POST.getlist("opt_name[]")
    opt_values = request.POST.getlist("opt_values[]")

    option_value_map = {}   # option_name → list of value strings

    for name, raw_vals in zip(opt_names, opt_values):
        name = name.strip()
        if not name:
            continue
        values = [v.strip() for v in raw_vals.split(",") if v.strip()]
        if not values:
            continue

        try:
            opt_obj = VariantOption.objects.create(product=product_obj, name=name)
        except Exception:
            opt_obj, _ = VariantOption.objects.get_or_create(product=product_obj, name=name)

        for val in values:
            try:
                VariantValue.objects.create(option=opt_obj, value=val)
            except Exception:
                pass

        option_value_map[name] = values

    # ── 3. PARSE VARIANT ROWS FROM FORM ──────────────────────────────────
    variant_rows = _parse_variants_from_post(request)

    # ── 4. SAVE VARIANTS ─────────────────────────────────────────────────
    used_skus = set()

    for idx, data in enumerate(variant_rows):
        # Parse attributes JSON
        attributes = {}
        raw_attrs = data.get("attributes", "")
        if raw_attrs:
            try:
                attributes = json.loads(raw_attrs)
            except (json.JSONDecodeError, TypeError):
                pass

        # Skip if no option attributes (means it's an empty row)
        if not attributes:
            continue

        regular_price = data.get("regular_price", "").strip()
        if not regular_price:
            continue  # Price is mandatory

        sale_price  = data.get("sale_price", "").strip()
        stock       = data.get("stock", "0").strip() or "0"
        points      = data.get("points", "").strip()
        description = data.get("description", "").strip()
        is_active   = data.get("is_active", "1") == "1"

        # Embed extra fields into attributes dict
        full_attributes = dict(attributes)  # copy
        if sale_price:
            full_attributes["sale_price"] = sale_price
        if points:
            full_attributes["points"] = points
        if description:
            full_attributes["description"] = description

        # ── SKU generation / uniqueness ──
        sku = data.get("sku", "").strip()
        if not sku:
            base     = (product_obj.name[:3] if product_obj.name else "VAR").upper()
            attr_str = "".join(str(v)[:2].upper() for v in attributes.values())
            sku      = f"{base}-{attr_str}-{idx}"

        # Ensure global uniqueness
        final_sku = sku
        counter   = 1
        while (
            final_sku in used_skus
            or ProductVariant.objects.filter(sku=final_sku).exists()
        ):
            final_sku = f"{sku}-{counter}"
            counter  += 1
        used_skus.add(final_sku)

        # ── Create variant ──
        try:
            variant = ProductVariant.objects.create(
                product    = product_obj,
                sku        = final_sku,
                price      = float(regular_price),
                stock      = int(stock),
                attributes = full_attributes,
                is_active  = is_active,
            )
        except IntegrityError:
            # attributes combination already exists — skip silently
            continue

        # ── Image (new upload takes priority, else keep existing) ──
        image_file = data.get("image")
        if image_file and hasattr(image_file, "read"):
            variant.image = image_file
            variant.save()
        else:
            existing_img = data.get("existing_image", "").strip()
            if existing_img:
                variant.image.name = existing_img
                variant.save()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN VIEW
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url="login")
def add_or_edit_product(request, pk=None):
    product_obj = get_object_or_404(Product, pk=pk) if pk else None

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product_obj)
        print(form.errors)
        if form.is_valid():
            with transaction.atomic():
                product_obj = form.save()

                # Gallery images
                gallery_images = request.FILES.getlist("gallery_images")
                if gallery_images:
                    for img in gallery_images:
                        ProductImage.objects.create(product=product_obj, image=img)

                product_type = request.POST.get("product_type", "simple")

                if product_type == "variable":
                    _handle_product_variants(product_obj, request, is_edit=bool(pk))
                else:
                    # Switched back to simple → clear variants
                    if pk:
                        product_obj.variants.all().delete()
                        product_obj.variant_options.all().delete()

            messages.success(
                request,
                f"Product '{product_obj.name}' {'updated' if pk else 'created'} successfully!"
            )
            return redirect("product")

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = ProductForm(instance=product_obj)

    # ── Context ──
    from .models import Category, Brand  # local import to avoid circular
    categories = Category.objects.all()
    brands     = Brand.objects.all()

    variant_options   = []
    existing_variants = []

    if product_obj and product_obj.product_type == "variable":
        variant_options   = product_obj.variant_options.all().prefetch_related("values")
        existing_variants = product_obj.variants.all()

    return render(request, "pages/add-product.html", {
        "form"             : form,
        "product"          : product_obj,
        "categories"       : categories,
        "brands"           : brands,
        "variant_options"  : variant_options,
        "existing_variants": existing_variants,
    })
   
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.warning(request, "Product deleted successfully!")
    return redirect('product') 

   
def product(request):
    search_query = request.GET.get('q', '')

    if search_query:
        products = Product.objects.filter(name__icontains=search_query).order_by('-id')
    else:
        products = Product.objects.all().order_by('-id')

    categories = Category.objects.all().order_by('-id')

    return render(request, "pages/product.html", {
        "products": products,
        "categories": categories,
    })


def get_point_settings():
    setting = PointSetting.objects.first()
    if not setting:
        setting = PointSetting(registration_bonus_points=settings.REGISTRATION_BONUS, point_value=settings.POINT_VALUE)
    return setting


@login_required(login_url='login')
def point_settings_view(request):
    setting, created = PointSetting.objects.get_or_create(
        defaults={'registration_bonus_points': settings.REGISTRATION_BONUS, 'point_value': settings.POINT_VALUE}
    )

    if request.method == 'POST':
        setting.registration_bonus_points = request.POST.get('registration_bonus_points', setting.registration_bonus_points)
        setting.point_value = request.POST.get('point_value', setting.point_value)
        setting.save()
        messages.success(request, "Point settings updated successfully!")
        return redirect('point_settings')

    context = {'setting': setting}
    return render(request, 'pages/point-settings.html', context)



# Redeem
@login_required(login_url='login')
def add_or_edit_redeem(request, pk=None):
    if pk:
        redeem = get_object_or_404(Redeem, pk=pk)
        success_message = "Redeem updated successfully "
    else:
        redeem = None
        success_message = "Redeem created successfully"

    if request.method == "POST":
        form = RedeemForm(request.POST, request.FILES, instance=redeem)
        if form.is_valid():
            redeem = form.save()
            messages.success(request, success_message)
            return redirect("redeem")
        else:
            print(form.errors)  
            messages.error(request, "Something went wrong, please try again") 
    else:
        form = RedeemForm(instance=redeem)

    return render(request, "pages/add-redeem.html", {
        "form": form,
        "redeem": redeem,
    })


@login_required(login_url='login')
def redeem_list(request):
    redeems = Redeem.objects.all().order_by('-created_at')
    return render(request, "pages/redeem.html", {
        "redeems": redeems,
    })

@login_required(login_url='login')
def delete_redeem(request, pk):
    redeem = get_object_or_404(Redeem, pk=pk)
    redeem.delete()
    messages.warning(request, "Redeem deleted successfully!")
    return redirect('redeem')

# Banner View
@login_required(login_url='login')
def add_or_edit_banner(request, pk=None):
    if pk:
        banner = get_object_or_404(Banner, pk=pk)
        success_message = "Banner updated successfully"
    else:
        banner = None
        success_message = "Banner created successfully"

    if request.method == "POST":
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("banner")
        else:
            messages.error(request, "Something went wrong, please try again ⚠️")
    else:
        form = BannerForm(instance=banner)

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, "pages/add-banner.html", {
        "form": form,
        "banner": banner,
        "categories": categories,
        "brands": brands,
        })


# Brand list with search
@login_required(login_url='login')
def banner(request):
    search_query = request.GET.get('q', '')
    if search_query:
        banners = Banner.objects.filter(name__icontains=search_query).order_by('-id')
    else:
        banners = Banner.objects.all().order_by('-id')

    return render(request, "pages/banner.html", {"banners": banners})


# 🔹 Delete Category
@login_required(login_url='login')
def delete_banner(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    banner.delete()
    messages.warning(request, "Brand deleted successfully!")
    return redirect('banner')


# AdBanner View
@login_required(login_url='login')
def add_or_edit_ad(request, pk=None):
    if pk:
        ad = get_object_or_404(Ad, pk=pk)
        success_message = "Ad-Banner updated successfully"
    else:
        ad = None
        success_message = "Ad-Banner created successfully"

    if request.method == "POST":
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("adbanner")
        else:
            messages.error(request, "Something went wrong, please try again ⚠️")
    else:
        form = AdForm(instance=ad)

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, "pages/add-adbanner.html", {
        "form": form,
        "ad": ad,
        "categories": categories,
        "brands": brands,
        })


# Brand list with search
@login_required(login_url='login')
def ad(request):
    search_query = request.GET.get('q', '')
    if search_query:
        ads = Ad.objects.filter(name__icontains=search_query).order_by('-id')
    else:
        ads = Ad.objects.all().order_by('-id')

    return render(request, "pages/adbanner.html", {"ads": ads})


#  Delete Category
@login_required(login_url='login')
def delete_ad(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    ad.delete()
    messages.warning(request, "Ad-Banner deleted successfully!")
    return redirect('adbanner')


# HeroBanner View
@login_required(login_url='login')
def add_or_edit_hero(request, pk=None):
    if pk:
        hero = get_object_or_404(Hero, pk=pk)
        success_message = "HeroBanner updated successfully"
    else:
        hero = None
        success_message = "HeroBanner created successfully"

    if request.method == "POST":
        form = HeroForm(request.POST, request.FILES, instance=hero)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("hero")
        else:
            messages.error(request, "Something went wrong, please try again ⚠️")
    else:
        form = HeroForm(instance=hero)

    return render(request, "pages/add-hero.html", {
        "form": form,
        "hero": hero,
        })


# Hero list with search
@login_required(login_url='login')
def hero(request):
    search_query = request.GET.get('q', '')
    if search_query:
        heros = Hero.objects.filter(title__icontains=search_query).order_by('-id')
    else:
        heros = Hero.objects.all().order_by('-id')

    return render(request, "pages/hero.html", {"heros": heros})


#  Delete Hero
@login_required(login_url='login')
def delete_hero(request, pk):
    ad = get_object_or_404(Hero, pk=pk)
    ad.delete()
    messages.warning(request, "HeroBanner deleted successfully!")
    return redirect('hero')



@login_required(login_url='login')
def create_discount(request, discount_pk=None):
   
    if discount_pk:
        discount = get_object_or_404(Discount, pk=discount_pk)
    else:
        discount = None

    products = Product.objects.all()
    users = AppUser.objects.all()

    if request.method == "POST":
        form = DiscountForm(request.POST, request.FILES, instance=discount)
        if form.is_valid():
            discount = form.save(commit=False)

            # Handle checkboxes safely
            apply_all_products = "apply_all_products" in request.POST
            apply_all_users = "apply_all_users" in request.POST

            discount.apply_all_products = apply_all_products
            discount.apply_all_users = apply_all_users
            discount.save()

        # Handle products
        if not apply_all_products:
            selected_products = request.POST.getlist("products")
            discount.products.set(selected_products)
        else:
            # Optional: if you want to automatically link all
            discount.products.set(Product.objects.all())

        #  Handle users
        if not apply_all_users:
            selected_users = request.POST.getlist("users")
            discount.users.set(selected_users)
        else:
            # Optional: link all users if “apply all” is checked
            discount.users.set(AppUser.objects.all())
            discount.save()
      
        send_discount_email(discount)
        messages.success(request, f"Discount '{discount.title}' created successfully!")
        return redirect("discount")  

    context = {
        "discount": discount,
        "products": products,
        "users": users,
    }
    return render(request, "pages/add-coupon.html", context)





@login_required(login_url='login')
def discount(request):
    discounts = Discount.objects.all()
    return render(request, "pages/coupons.html", {"discounts": discounts})

@login_required(login_url='login')
def delete_discount(request, pk):
    discount = get_object_or_404(Discount, pk=pk)
    discount.delete()
    messages.warning(request, f"Discount '{discount.title}' deleted successfully!")
    return redirect('discount')




def send_discount_email(discount):
    """Send email notification for a given discount."""
    users = AppUser.objects.all() if discount.apply_all_users else discount.users.all()

    for user in users:
        if not user.email:
            continue  

        subject = f"{discount.title} - Your Exclusive Discount Code!"
        from_email = "shahwaiz.dev@gmail.com"
        to = [user.email]

        html_content = render_to_string("emails/discount_coupon.html", {
            "user": user,
            "discount": discount,
        })

        msg = EmailMultiAlternatives(subject, "", from_email, to)
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
        except Exception as e:
            print(f"Failed to send to {user.email}: {e}")


def add_or_edit_rider(request, pk=None):
    rider = None
    cities = City.objects.all()

    if pk:
        rider = get_object_or_404(Rider, pk=pk)
        success_message = "Rider updated successfully"
    else:
        success_message = "Rider created successfully"

    if request.method == "POST":
        form = RiderForm(request.POST, instance=rider)

        if form.is_valid():
            rider = form.save(commit=False)

            # 🔥 PASSWORD FIX (IMPORTANT)
            raw_password = form.cleaned_data.get("password")
            if raw_password:
                if not raw_password.startswith("pbkdf2"):
                    rider.password = make_password(raw_password)

            rider.save()

            # 🔥 MANY TO MANY FIX (CITIES)
            form.save_m2m()

            messages.success(request, success_message)
            return redirect("rider_list")

        else:
            print(form.errors)
            messages.error(request, "Something went wrong, please try again ⚠️")

    else:
        form = RiderForm(instance=rider)

    return render(request, "pages/add_rider.html", {
        "form": form,
        "rider": rider,
        "cities": cities
    })

def rider_list(request):
    riders = Rider.objects.all().order_by("-id")

    return render(request, "pages/rider.html", {
        "riders": riders
    })

def delete_rider(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    rider.delete()

    messages.warning(request, "Rider deleted successfully")
    return redirect("rider_list")


def assign_rider(request, order_id, rider_id):
    order = get_object_or_404(Order, id=order_id)
    rider = get_object_or_404(Rider, id=rider_id)

    # City set nahi toh address se nikalo
    if not order.city:
        city_name = get_city_from_address(order.address)
        if city_name:
            try:
                city_obj = City.objects.get(name__iexact=city_name)
                order.city = city_obj
                order.save(update_fields=["city"])
            except City.DoesNotExist:
                pass

    if not order.city:
        messages.error(request, "Order City is not match")
        return redirect("order_list_ui")

    if order.city not in rider.cities.all():
        messages.error(request, f"Rider '{rider}' is not available in '{order.city.name}'")
        return redirect("order_list_ui")

    order.rider = rider
    order.status = "pending"
    order.save()

    messages.success(request, f"Rider assigned successfully")
    return redirect("order_list_ui")

def city_riders_popup(request, order_id, city_id):
    order = get_object_or_404(Order, id=order_id)
    city = get_object_or_404(City, id=city_id)

    riders = Rider.objects.filter(cities=city)

    return render(request, "include/rider_popup.html", {
        "order": order,
        "city": city,
        "riders": riders
    })



from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Rider










