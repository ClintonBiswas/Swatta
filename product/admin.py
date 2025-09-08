from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
from .models import FeatureCategory, OurProduct, ProductSubcategory, ProductColor, ProductBrand, ProductSizes,CustomerReview,ProductImage,CustomerQuestion, MyCart, CartItem, ShippingInformation, Order, OrderItem, ProductMoreSubCategory, ContactWithUs, PromoCode, Wishlist, ProductView, ScheduledMessage
# Register your models here.
admin.site.register(FeatureCategory)
admin.site.register(ProductSubcategory)
admin.site.register(ProductMoreSubCategory)
admin.site.register(ProductColor)
admin.site.register(ProductBrand)
admin.site.register(ProductSizes)
#admin.site.register(ProductImage)
admin.site.register(CustomerReview)
admin.site.register(CustomerQuestion)
admin.site.register(MyCart)
admin.site.register(CartItem)
admin.site.register(ShippingInformation)
#admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ContactWithUs)
admin.site.register(PromoCode)
admin.site.register(Wishlist)
admin.site.register(ProductView)

# @admin.register(OurProduct)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('product_name', 'product_category', 'product_price', 'discounted_price','product_brand')

# Custom Widget for multiple image upload
class MultipleImageInput(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['multiple'] = 'multiple'
        output = super().render(name, value, attrs, renderer)
        return mark_safe(output + '<p class="help">Hold Ctrl/Cmd to select multiple images</p>')

# Inline Form for Product Images
class ProductImageInlineForm(forms.ModelForm):
    image = forms.ImageField(widget=MultipleImageInput, required=False)

    class Meta:
        model = ProductImage
        fields = '__all__'

# Inline Admin for Product Images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageInlineForm
    extra = 5  # Show 5 empty forms by default
    fields = ('image', 'color', 'alt_text', 'display_order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"

# Main Product Admin
@admin.register(OurProduct)
class OurProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]  # Add the inline here
    list_display = ('product_name', 'main_image_preview', 'product_category', 'product_price', 'discounted_price','product_brand','view_count', 'last_viewed')
    readonly_fields = ('main_image_preview',)

    def main_image_preview(self, obj):
        if obj.product_image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.product_image.url)
        return "-"
    main_image_preview.short_description = "Main Image Preview"

# Register ProductImage if not using @admin.register
admin.site.register(ProductImage)


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'user', 'status', 'total_price', 'grand_total', 'created_at']
    readonly_fields = ['order_id']  # Make it visible but not editable

admin.site.register(Order, OrderAdmin)


@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(admin.ModelAdmin):
    list_display = ("message", "scheduled_time", "status", "send_to_all")
    list_filter = ("status", "send_to_all")
    search_fields = ("message",)
