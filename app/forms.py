from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Product, Redeem, Brand, ProductImage, Category, Banner, Ad, Hero, AppUser, Discount


# pehle widget define karo
class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'image']
  

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'slug', 'image']


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ["category", "brand", "image"]


class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ["category", "brand", "image"]


class HeroForm(forms.ModelForm):
    class Meta:
        model = Hero
        fields = ['title', 'subtext', 'image']


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            "name", "slug", "category", "brand",
            "short_description", "description",
            "image",
            "regular_price", "sale_price", "SKU", "quantity",
            "stock_status", "points", "product_type"
            
        ]

    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get("product_type")

        if product_type == "simple":
            if not cleaned_data.get("regular_price"):
                self.add_error("regular_price", "Regular price is required for simple products.")
            if not cleaned_data.get("SKU"):
                self.add_error("SKU", "SKU is required for simple products.")
        elif product_type == "variable":
            # Remove simple fields (they are not required for variable products)
            cleaned_data["regular_price"] = None
            cleaned_data["SKU"] = None

        return cleaned_data


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image" ]


class RedeemForm(forms.ModelForm):
    class Meta:
        model = Redeem
        fields = [
            "subtitle",
            "title",
            "description",
            "points_required",
            "image",
        ]


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = [
            "title",
            "code",
            "discount_type",
            "value",
            "start_date",
            "end_date",
            "apply_all_products",
            "apply_all_users",
        ]
    widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }



