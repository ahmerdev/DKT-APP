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
from .forms import CategoryForm, BrandForm, BannerForm, ProductForm, RedeemForm, AdForm, HeroForm, DiscountForm
from .models import Product, Redeem, ProductVariant, Category, Brand, ProductImage, Banner, Ad, Hero, Order, OrderItem, Payment, AppUser, Address, Discount

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# Dashborad Admin Panel User Login
def user_login(request):
    success_message = "User Login Successfully"
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            success_message = f"Welcome back, {user.username}!"
            messages.success(request, success_message)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


# Dashborad Admin Panel User Logout
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out")
    return redirect("login")

#  Home → Login redirect
def home(request):
    return redirect('login')


#  Dashboard (Protected)
@login_required(login_url='login')
def dashboard(request):
    return render(request, "dashboard.html")


# Dashboard App User List
def appuser_list_ui(request):
    users = AppUser.objects.all().order_by("-created_at")
    return render(request, "pages/customer-list.html", {"users": users})


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
    messages.warning(request, "Order deleted successfully!")
    return redirect('appuser_list')


# Admin App Customer Details
def customer_detail(request, pk):
    user = get_object_or_404(AppUser, pk=pk)

    # Details orders
    addresses = Address.objects.filter(user=user)
    orders = Order.objects.filter(status="delivered", user=user)
    normal_orders = orders.filter(type="normal")
    redeem_orders = orders.filter(type="redeem")

    normal_orders_data = []
    redeem_orders_data = []

    # Normal orders
    for order in normal_orders:
        items = order.items.all()
        order_points = sum(item.pts for item in items)
        normal_orders_data.append({
            "order": order,
            "items": items,
            "order_points": order_points,
        })

    # Redeem orders
    for order in redeem_orders:
        items = order.items.all()
        order_points = sum(item.pts for item in items)
        redeem_orders_data.append({
            "order": order,
            "items": items,
            "order_points": order_points,
        })

    # Calculate points
    earned_points = sum(i["order_points"] for i in normal_orders_data)
    spent_points = sum(i["order_points"] for i in redeem_orders_data)
    available_points = earned_points - spent_points

    context = {
        "user": user,
        "normal_orders_data": normal_orders_data,
        "redeem_orders_data": redeem_orders_data,
        "normal_orders": normal_orders,
        "redeem_orders": redeem_orders,
        "earned_points": earned_points,
        "spent_points": spent_points,
        "available_points": available_points,
        "addresses": addresses  
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



# List Orders UI
def order_list_ui(request):
    normal_orders = Order.objects.filter(type="normal").order_by("-created_at")
    redeem_orders = Order.objects.filter(type="redeem").order_by("-created_at")

    return render(request, "pages/order_list.html", {
        "normal_orders": normal_orders,
        "redeem_orders": redeem_orders,
    })


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


# Update Status UI
def update_order_status_ui(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")
        order.status = new_status
        order.save()
        return redirect("order_list_ui")

    return render(request, "pages/update_order.html", {"order": order})

@login_required(login_url='login')
def delete_order_ui(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.warning(request, "Order deleted successfully!")
    return redirect('order_list_ui')



def handle_product_variants(product, request, pk=None):
    """Save product variants if product_type == variable"""
    if request.POST.get("product_type") != "variable":
        return

    # Purge old variants on edit
    if pk:
        product.variants.all().delete()

    variants = defaultdict(dict)

    # collect POST fields
    for key, value in request.POST.items():
        if key.startswith("variants["):
            idx = key.split("[")[1].split("]")[0]
            field = key.split("[")[2].split("]")[0]
            variants[idx][field] = value

    # collect FILES (images)
    for key, file in request.FILES.items():
        if key.startswith("variants["):
            idx = key.split("[")[1].split("]")[0]
            field = key.split("[")[2].split("]")[0]
            variants[idx][field] = file

    # save each variant
    for idx, data in variants.items():
        # parse options json if present
        options = {}
        if "options" in data:
            try:
                options = json.loads(data["options"])
            except Exception:
                options = {}

        attributes = {
            "options": options,
            "sale_price": data.get("sale_price"),
            "points": data.get("points"),
            "description": data.get("description"),
        }

        try:
            variant = ProductVariant.objects.create(
                product=product,
                sku=data.get("sku") or None,
                price=data.get("regular_price") or 0,
                stock=data.get("stock") or 0,
                attributes=attributes,
            )

            uploaded_image = request.FILES.get(f"variants[{idx}][image]")
            if uploaded_image:
                variant.image = uploaded_image
            else:
                existing_image = request.POST.get(f"variants[{idx}][existing_image]")
                if existing_image:
                    variant.image.name = existing_image

            variant.save()
        except IntegrityError:
            messages.error(request, f"Duplicate SKU: {data.get('sku')}. Please use a unique SKU.")
            raise


# ----------------------------
#  Main View
# ----------------------------

@login_required(login_url='login')
def add_or_edit_product(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            with transaction.atomic():
                product = form.save()

                 # Save gallery images
                gallery_images = request.FILES.getlist("gallery_images")
                print("DEBUG → request.FILES keys:", request.FILES.keys())
                print("DEBUG → gallery_images list:", request.FILES.getlist("gallery_images"))
                if gallery_images:
                        for img in gallery_images:
                            ProductImage.objects.create(product=product, image=img)


                # Handle variants
                handle_product_variants(product, request, pk)

                #  Success message
                messages.success(
                    request,
                    f"Product '{product.name}' {'updated' if pk else 'created'} successfully!"
                )
                return redirect("product")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, "pages/add-product.html", {
        "form": form,
        "product": product,
        "categories": categories,
        "brands": brands,
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


# 🔹 Delete Category
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























 # title = request.POST.get("title")
        # code = request.POST.get("code")
        # discount_type = request.POST.get("discount_type")
        # value = request.POST.get("value")
        # start_date  = request.POST.get("start_date")
        # end_date = request.POST.get("end_date")
        # apply_all_products = "apply_all_products" in request.POST
        # apply_all_users = "apply_all_users" in request.POST

        # # Create the discount object
        # discount = Discount.objects.create(
        #     title=title,
        #     code=code,
        #     discount_type=discount_type,
        #     value=value,
        #     start_date=start_date,
        #     end_date=end_date,
        #     apply_all_products=apply_all_products,
        #     apply_all_users=apply_all_users,
        # )







# Send OTP API
# @api_view(["POST"])
# def send_otp(request):
#     phone = request.data.get("phone")
#     if not phone:
#         return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         verification = client.verify.v2.services(
#             settings.TWILIO_VERIFY_SERVICE_SID
#         ).verifications.create(to=phone, channel="sms")

#         return Response({"status": verification.status}, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Verify OTP API
# @api_view(["POST"])
# def verify_otp(request):
#     phone = request.data.get("phone")
#     code = request.data.get("code")

#     if not phone or not code:
#         return Response({"error": "Phone and code are required"}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         verification_check = client.verify.v2.services(
#             settings.TWILIO_VERIFY_SERVICE_SID
#         ).verification_checks.create(to=phone, code=code)

#         if verification_check.status == "approved":
#             # Yahan user create/login logic dalna hoga (agar DB use karna hai to)
#             return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
#         else:
#             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




#  @media only screen and (max-width: 600px) {
#   .lookBook__container {
#     flex-direction: column-reverse;
#   }
# } 