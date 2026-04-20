from django import forms
from django.utils.text import slugify
from django.forms.widgets import ClearableFileInput
from .models import Product, Rider, Redeem, Brand, ProductImage, Category, Banner, Ad, Hero, Privacy, About, ContactInfo, AppUser, Discount


# pehle widget define karo
class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class RiderForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Rider
        fields = ["name", "phone", "email", "password", "designation", "cities"]
        widgets = {
            "cities": forms.SelectMultiple(attrs={"class": "form-control"})
        }

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

class PrivacyForm(forms.ModelForm):
    class Meta:
        model = Privacy
        fields = ['p_title', 't_title', 'p_text', 't_text']

class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        fields = ['title', 'text']


class ContactInfoForm(forms.ModelForm):
    class Meta:
        model = ContactInfo
        fields = ['title', 'tagline', 'mailing_address', 'helpline_number', 'corporate_contact', 'email_generic', 'email_collaboration', 'email_hr', 'drop_us_line_text']



class ProductForm(forms.ModelForm):
 
    class Meta:
        image = forms.ImageField(required=False)
        model = Product
        fields = [
            "name", "slug", "category", "brand",
            "short_description", "description",
            "image",
            "cost_price", "regular_price", "sale_price", "sku", "quantity",
            "stock_status", "points", "product_type"
        ]
 
    # ── Slug: auto-unique ─────────────────────────────────────────────────
    def clean_slug(self):
        # Raw POST data se lo
        name = self.data.get("name", "").strip()
        slug = self.data.get("slug", "").strip()
    
        # Slug se generate karo, fallback name se
        if slug:
            base = slugify(slug)
        elif name:
            base = slugify(name)
        else:
            raise forms.ValidationError("Slug generate nahi ho saka.")
    
        if not base:
            raise forms.ValidationError("Valid slug generate nahi ho saka.")
    
        final_slug = base
        counter = 1
    
        qs = Product.objects.filter(slug=final_slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
    
        while qs.exists():
            final_slug = f"{base}-{counter}"
            counter += 1
            qs = Product.objects.filter(slug=final_slug)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
    
        return final_slug
 
    # ── Price fields: comma strip ─────────────────────────────────────────
    def _clean_price(self, field_name):
        val = self.cleaned_data.get(field_name)
        if val is None or val == "":
            return val
        try:
            return float(str(val).replace(",", "").strip())
        except (ValueError, TypeError):
            raise forms.ValidationError("Valid price enter karein (e.g. 1500 ya 1,500).")
 
    def clean_regular_price(self):
        return self._clean_price("regular_price")
 
    def clean_sale_price(self):
        return self._clean_price("sale_price")
 
    def clean_cost_price(self):
        return self._clean_price("cost_price")
 
    # ── Main clean ────────────────────────────────────────────────────────
    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get("product_type")
 
        if product_type == "simple":
            if not cleaned_data.get("regular_price"):
                self.add_error("regular_price", "Regular price is required for simple products.")
            if not cleaned_data.get("sku"):
                self.add_error("sku", "SKU is required for simple products.")
 
        elif product_type == "variable":
            # Simple fields variable products ke liye required nahi
            cleaned_data["regular_price"] = None
            cleaned_data["sku"] = None
 
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



