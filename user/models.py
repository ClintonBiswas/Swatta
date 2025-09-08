from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from tinymce.models import HTMLField
from django.contrib.sites.models import Site
from django.urls import reverse

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    join_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email


class HomeBanner(models.Model):
    title = models.CharField(max_length=120, blank=True)
    category = models.ForeignKey('product.FeatureCategory', on_delete=models.SET_NULL, null=True, blank=True)
    link_url = models.CharField(max_length=200, blank=True, null=True)
    banner_pic = models.ImageField(upload_to='banner_image/')

    def save(self, *args, **kwargs):
        if self.category:
            domain = Site.objects.get_current().domain
            path = reverse('product:category-products', args=[self.category.slug])
            self.link_url = f"http://{domain}{path}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-id']

class DeleveryPolicy(models.Model):
    title = models.CharField(max_length=150, blank=True, null= True)
    text = HTMLField()
    def __str__(self):
        return self.title
class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=150, blank=True, null= True)
    text = HTMLField()
    def __str__(self):
        return self.title
class ReturnPolicy(models.Model):
    title = models.CharField(max_length=150, blank=True, null= True)
    text = HTMLField()
    def __str__(self):
        return self.title

class AboutUs(models.Model):
    title = models.CharField(max_length=100)
    text = HTMLField()
    def __str__(self):
        return self.title

class TermsAndCondition(models.Model):
    title = models.CharField(max_length=150)
    text = HTMLField()
    def __str__(self):
        return self.title
    
class SubscribeEmail(models.Model):
    email = models.EmailField(max_length=254)
    def __str__(self):
        return self.email




