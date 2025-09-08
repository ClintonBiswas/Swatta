from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, HomeBanner, DeleveryPolicy, ReturnPolicy, PrivacyPolicy, TermsAndCondition, AboutUs, SubscribeEmail

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name",)}),  # ✅ Fix: Add comma to make it a tuple
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    list_display = ("email", "name", "is_staff", "is_active")
    search_fields = ("email", "name")
    ordering = ("email",)

# Register your models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(HomeBanner)
admin.site.register(DeleveryPolicy)
admin.site.register(PrivacyPolicy)
admin.site.register(ReturnPolicy)
admin.site.register(AboutUs)
admin.site.register(TermsAndCondition)
admin.site.register(SubscribeEmail)
