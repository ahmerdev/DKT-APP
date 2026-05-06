from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
from app import views, api_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('media-library/', include('media_library.urls')),
# custom login/logout
   path('login/', views.user_login, name='login'),
   path('rider/login/', views.rider_login, name='rider_login'),
   path('logout/rider/', views.user_logout, name='user_logout'),
   path('logout/', auth_views.LogoutView.as_view(), name='logout'),

#App User Route 
    path('appusers/', views.appuser_list_ui, name="appuser_list"),
    path('appuser/create/', views.create_appuser_ui, name="create_appuser"),
    path('appuser/update/<int:pk>/', views.create_appuser_ui, name="create_appuser"),
    path('appusers/<int:pk>/', views.user_status, name='user_status'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers-address/<int:pk>/', views.customer_address, name='customer_address'),
    path('customers-address-delete/<int:pk>/', views.customer_address_delete, name='customer_address_delete'),
    path("appusers/delete/<int:pk>/", views.delete_appuser_ui, name="delete_appuser"),
    path('settings/points/', views.point_settings_view, name='point_settings'),

# Dashboard 
    path('', views.home, name='home'),
    path("dashboard/", views.dashboard, name="dashboard"),
    path('reports/',  views.reports, name='reports'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('clear-notifications/', views.clear_notifications, name='clear_notifications'),

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


# Privacy & Terms Route
    path('add-privacy/', views.add_or_edit_privacy, name='add_privacy'),
    path("privacy/", views.privacy, name="privacy"),
    path('privacy-policy/', views.privacy_page, name='privacy_policy'),
    path('terms-conditions/', views.terms_page, name='terms_conditions'),
    path("edit-privacy/<int:pk>/", views.add_or_edit_privacy, name="edit_privacy"),
    path("privacy/delete/<int:pk>/", views.delete_privacy  , name="delete_privacy"),

# About Us Route
    path('add-about/', views.add_or_edit_about, name='add_about'),
    path("about/", views.about, name="about"),
    path("edit-about/<int:pk>/", views.add_or_edit_about, name="edit_about"),
    path("about/delete/<int:pk>/", views.delete_about  , name="delete_about"),    

# Contact Us Route
    path('add-contact/', views.add_or_edit_contact, name='add_contact'),
    path("contact/", views.contact, name="contact"),
    path("contact-form/", views.contactform_list, name="contact_form"),
    path('get-contactform/<int:pk>/', views.get_contact_form, name='get-contact-form'),
    path("edit-contact/<int:pk>/", views.add_or_edit_contact, name="edit_contact"),
    path("contact/delete/<int:pk>/", views.delete_contact  , name="delete_contact"),
    path("contactform/delete/<int:pk>/", views.delete_contactform  , name="delete_contactform"),


# Product Route
    path('update-order/', views.update_product_order, name='update-order'),
    path('update-category-order/', views.update_category_order, name='update-category-order'),
    path('update-brand-order/', views.update_brand_order, name='update-brand-order'),
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

# Rider Route
    path("riders/", views.rider_list, name="rider_list"),
    path("riders/add/", views.add_or_edit_rider, name="add_rider"),
    path("riders/edit/<int:pk>/", views.add_or_edit_rider, name="edit_rider"),
    path("riders/delete/<int:pk>/", views.delete_rider, name="delete_rider"),
    path("rider/forgot-password/", views.rider_forgot_password, name="rider_forgot_password"),
    path("rider/reset-password/<uuid:token>/", views.rider_reset_password, name="rider_reset_password"),

# AdBanner Route
    path('add-hero/', views.add_or_edit_hero, name='add_hero'),
    path("hero/", views.hero, name="hero"),
    path("edit-hero/<int:pk>/", views.add_or_edit_hero, name="edit_hero"),
    path("heros/delete/<int:pk>/", views.delete_hero, name="delete_hero"),
 
# Order Route 
    path('orders/', views.order_list_ui, name="order_list_ui"),
    path('orders/create/', views.create_order_ui, name="create_order_ui"),
    path('orders/update/<int:pk>/', views.update_order_status_ui, name="update_order_status_ui"),
    path("city-riders/<int:order_id>/<int:city_id>/", views.city_riders_popup, name="city_riders_popup"),
    path("orders/assign/<int:order_id>/<int:rider_id>/", views.assign_rider, name="assign_rider"),
    path("orders/delete/<int:pk>/", views.delete_order_ui, name="delete_order_ui"),


# Discounts Route 
    path('discounts/', views.discount, name="discount"),
    path('discounts/create/', views.create_discount, name="create_discount"),
    path("discounts/delete/<int:pk>/", views.delete_discount, name="delete_discount"),
    path('discount-popup/add/', views.add_or_edit_discount_popup, name="add-discount-popup"),
    path('discount-popup/edit/<int:pk>/', views.add_or_edit_discount_popup, name="edit-discount-popup"),
    path('discount-popup/', views.discount_popup_list, name="discount-popup-list"),
    path('delete-discount-popup/<int:pk>/', views.delete_discount_popup, name='delete-discount-popup'),
    

# Review Route
    path("reviews/", views.reviews, name="review"),
    path("review/delete/<int:pk>/", views.delete_review, name="delete_review"),
# ->orderByRaw('(product_images.src IS NOT NULL AND products.regular_price IS NOT NULL) DESC')
#             ->orderBy('products.regular_price', 'asc')


    # Rider APIs
    path('api/rider/login/', api_view.rider_login_api, name='rider_login_api'),
    path('api/rider/forgot-password/', api_view.rider_forgot_password_api, name='rider_forgot_password_api'),
    path('api/rider/reset-password/', api_view.rider_reset_password_api, name='rider_reset_password_api'),
    path('api/rider/orders/<int:rider_id>/', api_view.rider_orders_api, name='rider_orders_api'),
    path('api/rider/orders/<int:order_id>/update-status/', api_view.rider_update_order_status_api, name='rider_update_order_status_api'),
    path('api/categories/', api_view.category_list_api, name='api_category_list'),
    path('api/brands/', api_view.brand_list_api, name='api_brand_list'),
    path('api/privacy/', api_view.privacy_content_api, name='api_privacy_content'),
    path('api/about/', api_view.about_content_api, name='api_about_content'),
    path('api/contact/', api_view.contact_content_api, name='api_contact_content'),
    path('api/banners/', api_view.banner_list_api, name='api_banner_list'),
    path('api/ads/', api_view.ad_list_api, name='api_ad_list'),
    path('api/heros/', api_view.hero_list_api, name='api_hero_list'),
    path("api/products/", api_view.product_list_api, name="product-list-api"),
    path("api/redeems/", api_view.redeem_list_api, name="redeem-list-api"),
    path("api/discounts/", api_view.validate_discount_api, name="validate-discount-api"),
    # path("api/send-otp/", api_view.send_otp, name="send-otp"),
    # path("api/verify-otp/", api_view.verify_otp, name="verify-otp"),
    path("api/create-order/", api_view.create_order, name="create_order"),
    path("api/create-form/", api_view.create_contact, name="create_form"),
    path("api/create-review/", api_view.create_review, name="create_review"),
   
    path("api/update-order-status/<int:order_pk>/", api_view.update_order_status, name="update_order_status"),
    path("api/orders/", api_view.list_orders, name="list-orders"),
    path('api/app-users/', api_view.create_app_user, name='create_app_user'),
    path('api/complete_profile/', api_view.complete_profile, name='complete_profile'),
    path('api/app-users/verify-otp/',api_view.verify_otp, name='verify_otp'),
    path('api/app-users/resend_otp/',api_view.resend_otp, name='resend_otp'),
    path("api/forgot-password/", api_view.forgot_password),
    path("api/reset-password/", api_view.reset_password),
    path('api/app-user-address/<int:pk>/', api_view.create_user_address, name='create_user_address'),
    path('api/deactivate/<int:pk>/', api_view.deactivate_account, name='deactivate-account'),
    path('api/toggle/<str:model_name>/<int:pk>/', api_view.toggle_is_active, name='toggle-status'),
    path('api/delete-user-address/<int:pk>/', api_view.delete_user_address, name='delete_user_address'),
    path("api/update-user/<int:user_pk>/", api_view.update_profile_view, name="update_profile"),
    path("api/account-delete/<int:pk>/", api_view.account_delete, name="account_delete"),
    path("api/app-user/list/", api_view.app_user_list, name="app_user_list"),
    path('api/app-user/login/', api_view.app_user_login, name='app_user_login'),
    # path("api/products/<int:pk>/", views.product_detail_api, name="product-detail-api"),
    # path("api/products/<int:product_id>/variants/", views.product_variants_api, name="product-variants-api"),
    # path("api/products/<int:product_id>/options/", views.product_options_api, name="product-options-api"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






