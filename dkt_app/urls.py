from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from app import views, api_view


urlpatterns = [
    path('admin/', admin.site.urls),

# custom login/logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

#App User Route 
    path('appusers/', views.appuser_list_ui, name="appuser_list"),
    path('appuser/create/', views.create_appuser_ui, name="create_appuser"),
    path('appuser/update/<int:pk>/', views.create_appuser_ui, name="create_appuser"),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers-address/<int:pk>/', views.customer_address, name='customer_address'),
    path('customers-address-delete/<int:pk>/', views.customer_address_delete, name='customer_address_delete'),
    path("appusers/delete/<int:pk>/", views.delete_appuser_ui, name="delete_appuser"),

# Dashboard 
    path('', views.home, name='home'),
    path("dashboard/", views.dashboard, name="dashboard"),

# Category Route
    path('add-category/', views.add_or_edit_category, name='add_category'),
    path("category/", views.category, name="category"),
    path("edit-category/<int:pk>/", views.add_or_edit_category, name="edit_category"),
    path("categories/delete/<int:pk>/", views.delete_category, name="delete_category"),

# Brand Route
    path('add-brand/', views.add_or_edit_brand, name='add_brand'),
    path("brand/", views.brand, name="brand"),
    path("edit-brand/<int:pk>/", views.add_or_edit_brand, name="edit_brand"),
    path("brands/delete/<int:pk>/", views.delete_brand  , name="delete_brand"),

# Product Route
    path('product/', views.product, name='product'),
    path("product/add/", views.add_or_edit_product, name="add_product"),
    path('product/<int:pk>/edit/', views.add_or_edit_product, name='edit_product'),
    path("products/delete/<int:pk>/", views.delete_product, name="delete_product"),


# Redeem Route
    path('redeem/', views.redeem_list, name='redeem'),
    path("redeem/add/", views.add_or_edit_redeem, name="add_redeem"),
    path('redeem/<int:pk>/edit/', views.add_or_edit_redeem, name='edit_redeem'),
    path("redeems/delete/<int:pk>/", views.delete_redeem, name="delete_redeem"),

# Banner Route
    path('add-banner/', views.add_or_edit_banner, name='add_banner'),
    path("banner/", views.banner, name="banner"),
    path("edit-banner/<int:pk>/", views.add_or_edit_banner, name="edit_banner"),
    path("banners/delete/<int:pk>/", views.delete_banner  , name="delete_banner"),


# AdBanner Route
    path('add-adbanner/', views.add_or_edit_ad, name='add_adbanner'),
    path("adbanner/", views.ad, name="adbanner"),
    path("edit-adbanner/<int:pk>/", views.add_or_edit_ad, name="edit_adbanner"),
    path("adbanners/delete/<int:pk>/", views.delete_ad  , name="delete_adbanner"),


# AdBanner Route
    path('add-hero/', views.add_or_edit_hero, name='add_hero'),
    path("hero/", views.hero, name="hero"),
    path("edit-hero/<int:pk>/", views.add_or_edit_hero, name="edit_hero"),
    path("heros/delete/<int:pk>/", views.delete_hero, name="delete_hero"),
 
# Order Route 
    path('orders/', views.order_list_ui, name="order_list_ui"),
    path('orders/create/', views.create_order_ui, name="create_order_ui"),
    path('orders/update/<int:pk>/', views.update_order_status_ui, name="update_order_status_ui"),
    path("orders/delete/<int:pk>/", views.delete_order_ui, name="delete_order_ui"),


# Discounts Route 
    path('discounts/', views.discount, name="discount"),
    path('discounts/create/', views.create_discount, name="create_discount"),
    path("discounts/delete/<int:pk>/", views.delete_discount, name="delete_discount"),

# ->orderByRaw('(product_images.src IS NOT NULL AND products.regular_price IS NOT NULL) DESC')
#             ->orderBy('products.regular_price', 'asc')
# API
    path('api/categories/', api_view.category_list_api, name='api_category_list'),
    path('api/brands/', api_view.brand_list_api, name='api_brand_list'),
    path('api/banners/', api_view.banner_list_api, name='api_banner_list'),
    path('api/ads/', api_view.ad_list_api, name='api_ad_list'),
    path('api/heros/', api_view.hero_list_api, name='api_hero_list'),
    path("api/products/", api_view.product_list_api, name="product-list-api"),
    path("api/redeems/", api_view.redeem_list_api, name="redeem-list-api"),
    path("api/discounts/", api_view.validate_discount_api, name="validate-discount-api"),
    # path("api/send-otp/", api_view.send_otp, name="send-otp"),
    # path("api/verify-otp/", api_view.verify_otp, name="verify-otp"),
    path("api/create-order/", api_view.create_order, name="create_order"),
    path("api/update-order-status/<int:order_pk>/", api_view.update_order_status, name="update_order_status"),
    path("api/orders/", api_view.list_orders, name="list-orders"),
    path('api/app-users/', api_view.create_app_user, name='create_app_user'),
    path('api/app-user-address/<int:pk>/', api_view.create_user_address, name='create_user_address'),
     path('api/delete-user-address/<int:pk>/', api_view.delete_user_address, name='delete_user_address'),
    path("api/update-user/<int:user_pk>/", api_view.update_profile_view, name="update_profile"),
    path("api/account-delete/<int:pk>/", api_view.account_delete, name="account_delete"),
    path("api/app-user/list/", api_view.app_user_list, name="app_user_list"),
    path('api/app-user/login/', api_view.app_user_login, name='app_user_login'),
    # path("api/products/<int:pk>/", views.product_detail_api, name="product-detail-api"),
    # path("api/products/<int:product_id>/variants/", views.product_variants_api, name="product-variants-api"),
    # path("api/products/<int:product_id>/options/", views.product_options_api, name="product-options-api"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






