from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm
app_name = 'user'

urlpatterns = [
    path('', views.HomeView, name='home'),
    path('products/<slug:category_slug>/<slug:subcategory_slug>/', views.products_by_subcategory, name='products_by_subcategory'),
    path("get-products/", views.get_products_by_brand, name="get_all_products"),
    path('get-products-by-brand/<str:brand_id>/', views.get_products_by_brand, name='get_products_by_brand'),
    path('login/', views.LoginView, name='login'),
    path('register/', views.RegisterView, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.html',
        form_class=CustomPasswordResetForm  # 👈 Use the custom form
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('profile/', views.user_profile, name='profile'),
    path('return-policy/', views.ReturnPolicyView, name='return-policy'),
    path('delivery-policy/', views.DeliveryPrivacyView, name='delivery-policy'),
    path('privacy-policy/', views.PrivacyView, name='privacy-policy'),
    path('about-us/', views.AboutUsView, name='about'),
    path('terms-and-condition/', views.TermsAndConditionView, name='terms-and-condition'),
    path('most-view-product/', views.MostViewProduct, name='most-view-product'),
]