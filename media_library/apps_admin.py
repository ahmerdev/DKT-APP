## ── apps.py ──────────────────────────────────────────────────
## File: media_library/apps.py

from django.apps import AppConfig

class MediaLibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'media_library'
    verbose_name       = 'Media Library'


## ── admin.py ─────────────────────────────────────────────────
## File: media_library/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import MediaFile


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display  = ['thumbnail', 'name', 'folder', 'size_display', 'uploaded_at']
    list_filter   = ['folder', 'uploaded_at']
    search_fields = ['name']
    readonly_fields = ['thumbnail_large', 'size_display', 'uploaded_at']

    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover;border-radius:6px;">',
                obj.image.url
            )
        return '—'
    thumbnail.short_description = 'Preview'

    def thumbnail_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;border-radius:10px;">',
                obj.image.url
            )
        return '—'
    thumbnail_large.short_description = 'Image Preview'
