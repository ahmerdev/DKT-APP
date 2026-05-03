from django.db import models
from django.utils import timezone
import os


class MediaFile(models.Model):
    """
    Global Media Library — har uploaded image yahan store hogi
    Shopify jesa centralized media system
    """
    FOLDER_CHOICES = [
        ('general',  'General'),
        ('products', 'Products'),
        ('banners',  'Banners'),
        ('brands',   'Brands'),
        ('category', 'Category'),
        ('users',    'Users'),
        ('ads',      'Ads'),
        ('heros',    'Heroes'),
        ('redeem',   'Redeem'),
    ]

    image       = models.ImageField(upload_to='media_library/')
    name        = models.CharField(max_length=255, blank=True)
    folder      = models.CharField(max_length=50, choices=FOLDER_CHOICES, default='general')
    uploaded_at = models.DateTimeField(default=timezone.now)
    file_size   = models.PositiveIntegerField(default=0, help_text="bytes")

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name or os.path.basename(self.image.name)

    def save(self, *args, **kwargs):
        # Auto name set karo agar blank hai
        if not self.name and self.image:
            self.name = os.path.basename(self.image.name)
        super().save(*args, **kwargs)
        # File size save karo
        if self.image and os.path.exists(self.image.path):
            self.file_size = os.path.getsize(self.image.path)
            MediaFile.objects.filter(pk=self.pk).update(file_size=self.file_size)

    def delete(self, *args, **kwargs):
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)

    @property
    def size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size // 1024} KB"
        else:
            return f"{self.file_size // (1024 * 1024)} MB"
