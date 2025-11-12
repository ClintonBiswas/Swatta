from django.shortcuts import render, redirect, get_object_or_404 
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .models import HomeBanner, CustomUser, ReturnPolicy, DeleveryPolicy, PrivacyPolicy, AboutUs, TermsAndCondition, SubscribeEmail
from product.models import FeatureCategory, ProductBrand, OurProduct, ProductMoreSubCategory
from django.core.paginator import Paginator
from product.models import Order, ShippingInformation
from blog.models import MyBlog
from .utils import get_popular_products
from product.utils import send_event
from pool.utils import get_client_ip

# Create your views here.

def HomeView(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        email = request.POST.get('subscribe_email')
        if SubscribeEmail.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'This email is already subscribed.'})
        else:
            SubscribeEmail.objects.create(email=email)
            return JsonResponse({'status': 'success', 'message': 'Successfully subscribed to our newsletter.'})

    banner = HomeBanner.objects.all()
    feature_category = FeatureCategory.objects.all()
    product_brands = ProductBrand.objects.all()
    all_products = OurProduct.objects.all()
    feature_products = OurProduct.objects.filter(product_sub_category__title='Featured Products')
    trending_products = OurProduct.objects.filter(product_sub_category__title='Trending Products')
    popular_products = get_popular_products(limit=10)
    
    discount_products = OurProduct.objects.filter(
        product_category__discount__gte=20
    ).select_related('product_category')
    
    blogs = MyBlog.objects.all()

    event_id = request.COOKIES.get("fb_event_id")

    send_event(
        event_name="PageView",
        event_id=event_id,
        user_data={
            "client_ip_address": get_client_ip(request),
            "client_user_agent": request.META.get("HTTP_USER_AGENT"),
            "fbc": [request.COOKIES.get("_fbc")] if request.COOKIES.get("_fbc") else [],
            "fbp": [request.COOKIES.get("_fbp")] if request.COOKIES.get("_fbp") else [],
        },
        custom_data={
            "page_path": request.path,
            "page_title": getattr(request, "title", "Home"),
            "value": 1.0,
            "currency": "BDT",
            "content_ids": [request.path],
            "content_category": "PageView",
            "event_source_url": request.build_absolute_uri(),
        },
    )


    context = {
        'banners': banner,
        'feature_categories': feature_category,
        'popular_products': popular_products,
        'product_brands': product_brands,
        'all_products': all_products,
        'feature_products': feature_products,
        'trending_products': trending_products,
        'discount_products': discount_products,
        'blogs': blogs,
    }
    return render(request, 'user/home.html', context)

def MostViewProduct(request):
    popular_products = get_popular_products(limit=20)
    return render(request, 'user/most_view_product.html', context={'popular_products':popular_products})

def products_by_subcategory(request, category_slug, subcategory_slug):
    category = get_object_or_404(FeatureCategory, slug=category_slug)
    subcategory = get_object_or_404(ProductMoreSubCategory, slug=subcategory_slug, category=category)
    products = OurProduct.objects.filter(
        product_category=category,
        product_more_sub_category=subcategory
    )
    return render(request, 'user/subcategory_product.html', {
        'products': products,
        'category': category,
        'subcategory': subcategory
    })

def get_products_by_brand(request, brand_id=None):
    """Fetch products based on the selected brand with pagination"""
    page = request.GET.get('page', 1)
    items_per_page = 10
    
    if not brand_id or brand_id == "all":
        products = OurProduct.objects.all().order_by('-created_at')
    else:
        brand = get_object_or_404(ProductBrand, id=brand_id)
        products = OurProduct.objects.filter(product_brand=brand).order_by('-created_at')
    
    paginator = Paginator(products, items_per_page)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    products_data = []
    for product in page_obj:
        products_data.append({
            "id": product.id,
            "product_name": product.product_name,
            "product_price": str(product.product_price),
            "discounted_price": str(product.discounted_price()),
            "product_slug": product.product_slug,
            "product_image": request.build_absolute_uri(product.product_image.url) if product.product_image else "",
            "average_rating": product.average_rating(),  # Call the method
            "total_reviews": product.total_reviews(),    # Call the method
            "brand_name": product.product_brand.title if product.product_brand else None,
            "product_details": product.product_details,
            "product_code": product.product_code,
            "product_status": product.product_status,
            #"product_type": product.product_type,
            "product_category": product.product_category.title if product.product_category else None,
            "product_sub_category": product.product_sub_category.title if product.product_sub_category else None,
            "product_colors": [color.name for color in product.product_colors.all()],
            "product_size": [size.title for size in product.product_size.all()], 
        })
    
    return JsonResponse({
        "products": products_data,
        "has_next": page_obj.has_next(),
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages
    })

def LoginView(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or reverse('user:home')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password. Please try again.")
            return redirect('user:login')
    
    context = {
        'next': request.GET.get('next', '')
    }
    return render(request, template_name='user/login.html', context=context)

def RegisterView(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        #phone = request.POST.get('phone')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # phone_validator = RegexValidator(
        #     regex=r"^01[3-9]\d{8}$",
        #     message="Invalid phone number! Must start with 013-019 and have exactly 11 digits."
        # )
        # try:
        #     phone_validator(phone)  
        # except ValidationError as e:
        #     messages.error(request, str(e))
        #     return redirect('user:register')

        if len(password1) < 6:
            messages.error(request, "Password must be at least 6 characters long!")
            return redirect('user:register')
        if password1 != password2:
            messages.error(request, "Password don't match!")
            return redirect('user:register')
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email is already taken!')
            return redirect('user:register')
        user = CustomUser.objects.create_user(email=email, password=password1, name=name)
        user.save()
        return redirect('user:login')
    dict = {}
    return render(request, template_name='user/register.html', context=dict)

def logout_view(request):
    logout(request)
    return redirect('user:home')

def user_profile(request):
    user = request.user
    try:
        user_info = CustomUser.objects.get(email=user.email)
        customer_info = ShippingInformation.objects.filter(user=user).last()
        # Get all orders for the user with their items
        orders = Order.objects.filter(user=user, is_verified = True)\
                      .order_by('-created_at')\
                      .prefetch_related('order_items__product')
        
        context = {
            'user_info': user_info,
            'orders': orders,  # Pass all orders to template
            'customer_info':customer_info,
        }
        return render(request, 'user/user_profile.html', context)
        
    except CustomUser.DoesNotExist:
        return redirect('login')
        
    except CustomUser.DoesNotExist:
        # Handle case where user doesn't exist
        return redirect('login')

def PrivacyView(request):
    info = PrivacyPolicy.objects.first()
    return render(request, 'user/privacy.html', context={'info':info})
def DeliveryPrivacyView(request):
    info = DeleveryPolicy.objects.first()
    return render(request, 'user/delivery_privacy.html', context={'info':info})
def ReturnPolicyView(request):
    info = ReturnPolicy.objects.first()
    return render(request, 'user/return_policy.html', context={'info':info})
def AboutUsView(request):
    info = AboutUs.objects.first()
    return render(request, 'user/about_us.html', context={'info':info})
def TermsAndConditionView(request):
    info = TermsAndCondition.objects.first()
    return render(request, 'user/termsandcondition.html', context={'info':info})


        

