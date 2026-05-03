from django.urls import path
from . import views

urlpatterns = [
    # Full media library page
    path('',                      views.media_library_page, name='media_library'),

    # AJAX APIs
    path('api/picker/',           views.media_picker_api,   name='media_picker_api'),
    path('api/upload/',           views.media_upload_api,   name='media_upload_api'),
    path('api/delete/<int:pk>/',  views.media_delete_api,   name='media_delete_api'),
]
