from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import OurProduct, ProductImage, MyCart, CartItem, ShippingInformation, OrderItem, Order, ProductBrand, FeatureCategory, ProductSubcategory, PromoCode, Wishlist, ProductView, ProductMoreSubCategory
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import ProductReviewForm, ShippingInformationForm, ContactWithUsForm, ScheduledMessageForm
import json, random, time, re, logging, traceback
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import transaction
from django.db.models import F, DecimalField, ExpressionWrapper, Avg, Count
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg
from datetime import datetime
from .tasks import send_verification_code_task
from urllib.parse import urlparse, parse_qs
from django.core.validators import validate_email
from django.core.exceptions import ValidationError 
from django.core.signing import Signer
from django.conf import settings
from .utils import normalize_phone, get_guest_phone_from_cookie
from django.template.loader import render_to_string
from user.utils import get_popular_products
from .utils import send_event
from .utils import normalize_user_data
from pool.utils import get_client_ip

logger = logging.getLogger(__name__)
# Create your views here.

def CategoryProducts(request, slug):
    try:
        category = get_object_or_404(FeatureCategory, slug=slug)

        # Get all subcategories and brands for this category
        subcategories = ProductMoreSubCategory.objects.filter(category=category)
        brands = ProductBrand.objects.filter(
            id__in=OurProduct.objects.filter(product_category=category)
            .values_list('product_brand', flat=True).distinct()
        )

        # Prepare discount expression based on category discount
        category_discount = category.discount or Decimal(0)
        discount_expr = ExpressionWrapper(
            F('product_price') - (F('product_price') * Decimal(category_discount) / Decimal(100)),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )

        # Annotated queryset
        category_product = OurProduct.objects.filter(product_category=category).annotate(
            calculated_avg_rating=Avg('reviews__rating'),
            calculated_total_reviews=Count('reviews'),
            calculated_discounted_price=discount_expr
        )

        # Apply subcategory filter
        subcategory_filter = request.GET.get('subcategory')
        if subcategory_filter:
            category_product = category_product.filter(
                product_more_sub_category__slug=subcategory_filter
            )

        # Apply brand filter
        brand_filter = request.GET.get('brand')
        if brand_filter:
            category_product = category_product.filter(
                product_brand__slug=brand_filter
            )

        # Apply sorting
        sort_by = request.GET.get('sort_by', '')
        if sort_by == 'most_viewed':
            category_product = category_product.order_by('-view_count')
        elif sort_by == 'price_low_high':
            category_product = category_product.order_by('calculated_discounted_price')
        elif sort_by == 'price_high_low':
            category_product = category_product.order_by('-calculated_discounted_price')
        elif sort_by == 'most_rated':
            category_product = category_product.order_by('-calculated_total_reviews', '-calculated_avg_rating')
        else:
            category_product = category_product.order_by('-id')
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(category_product, 10)
        products = paginator.get_page(page)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            product_list = []
            for product in products:
                product_list.append({
                    "id": product.id,
                    "product_name": product.product_name,
                    "product_price": str(product.product_price),
                    "discounted_price": str(product.discounted_price()),
                    "product_slug": product.product_slug,
                    "product_image": request.build_absolute_uri(product.product_image.url) if product.product_image else "",
                    "average_rating": product.average_rating(),  
                    "total_reviews": product.total_reviews(),    
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
                'products': product_list,
                'has_next': products.has_next(),
                'next_page': products.next_page_number() if products.has_next() else None
            })
        
        context = {
            'category_product': products,
            'category': category,
            'subcategories': subcategories,
            'brands': brands,
        }
        return render(request, 'product/categorybrandproduct.html', context)
    

    except Exception as e:
        logger.error("AJAX CategoryProducts Error: %s", traceback.format_exc())
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        raise


def extract_youtube_id(url):
    parsed_url = urlparse(url)

    # Handle https://www.youtube.com/watch?v=xxxx
    if "youtube.com/watch" in url:
        return parse_qs(parsed_url.query).get("v", [None])[0]

    # Handle https://youtu.be/xxxx
    if "youtu.be" in url:
        return parsed_url.path.lstrip("/")

    # Handle https://www.youtube.com/embed/xxxx
    if "youtube.com/embed" in url:
        return parsed_url.path.split("/")[-1]

    return None

logger = logging.getLogger(__name__)
def track_product_view(request, product_slug):
    session_key = f'viewed_product_{product_slug}'
    
    if request.session.get(session_key):
        return JsonResponse({'status': 'skipped'})

    try:
        with transaction.atomic():
            product = OurProduct.objects.select_for_update().get(product_slug=product_slug)
            ProductView.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                ip_address=request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            product.increment_view_count()
            request.session[session_key] = True
            return JsonResponse({'status': 'success'})
            
    except OurProduct.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)
    except Exception as e:
        logger.exception("Tracking failed")
        return JsonResponse({'status': 'error'}, status=500)

def ProductDetails(request, product_slug):
    order_video_url = "https://www.youtube.com/watch?v=1CKU8BF-goM"
    product = get_object_or_404(OurProduct, product_slug=product_slug)
    product.video_id = extract_youtube_id(product.video_url) if product.video_url else None
    how_to_order_id = extract_youtube_id(order_video_url)
    product_category = product.product_category
    products_category = get_popular_products(limit=10, days=30, category=product_category)
    
    # Get first color or None if no colors exist
    first_color = product.product_colors.first()
    product_multiple_images = ProductImage.objects.filter(product=product).order_by('display_order')

    # ===== Server-Side ViewContent Pixel =====
    user_em = [request.user.email] if request.user.is_authenticated and getattr(request.user, 'email', None) else []
    user_ph = [getattr(request.user, 'phone_number', '')] if request.user.is_authenticated else []
    user_fullname = [request.user.fullname] if request.user.is_authenticated and getattr(request.user, 'fullname', None) else []

    send_event(
        event_name="ViewContent",
        user_data={
            "em": user_em,
            "ph": user_ph,
            "fn": user_fullname,  # use fullname here
            "client_ip_address": get_client_ip(request),
            "client_user_agent": request.META.get("HTTP_USER_AGENT"),
        },
        custom_data={
            "content_ids": [product.product_code],
            "content_name": product.product_name,
            "currency": "BDT",
            "value": float(product.discounted_price()),
        }
    )

    
    # Initialize color_images dictionary
    color_images = {}
    for color in product.product_colors.all():
        images = ProductImage.objects.filter(product=product, color=color).order_by('display_order')
        color_images[color.id] = {
            'name': color.name,
            'images': [{
                'url': image.image.url,
                'alt_text': image.alt_text or product.product_name,
                'display_order': image.display_order
            } for image in images]
        }
    
    # Handle AJAX requests
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Check if it's a review submission
        if 'rating' in request.POST:
            form = ProductReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.product = product
                
                if request.user.is_authenticated:
                    review.user = request.user
                    if not review.name and request.user.name:
                        review.name = request.user.name
                else:
                    review.user = None
                    review.name = form.cleaned_data.get('name', '')
                
                review.save()
                
                # Return success response with new review data
                return JsonResponse({
                    'success': True,
                    'message': 'Review submitted successfully!',
                    'review': {
                        'name': review.get_display_name(),
                        'rating': review.rating,
                        'comment': review.comment,
                        'created_at': review.created_at.strftime('%B %d, %Y')
                    }
                })
            else:
                # Return form errors
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        
        # Handle color image requests (existing code)
        color_id = request.POST.get('color_id')
        images = list(ProductImage.objects.filter(product=product, color_id=color_id)
                      .values('image', 'alt_text', 'display_order')
                      .order_by('display_order'))
        return JsonResponse({'images': images})
    
    # Handle regular POST requests (non-AJAX fallback)
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            
            if request.user.is_authenticated:
                review.user = request.user
                if not review.name and request.user.name:
                    review.name = request.user.name
            else:
                review.user = None
                review.name = form.cleaned_data.get('name', '')
            
            review.save()
    
    # Handle GET requests
    form = ProductReviewForm()
    
    # Implement pagination for reviews
    all_reviews = product.reviews.all()
    paginator = Paginator(all_reviews, 3)  # Show 3 reviews per page
    page_number = request.GET.get('page')
    reviews_page = paginator.get_page(page_number)
    
    context = { 
        'products': product,
        'products_category': products_category,
        'product_multiple_images': product_multiple_images,
        'form': form,
        'how_to_order_id': how_to_order_id,
        'color_images': color_images,
        'first_color_id': first_color.id if first_color else None,
        'reviews_page': reviews_page,  # Add paginated reviews
    }
    return render(request, 'product/product-details.html', context=context)

@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            quantity = int(data.get("quantity", 1))
            size = data.get("size", None)
            color = data.get("color", None)

            product = get_object_or_404(OurProduct, id=product_id)

            if request.user.is_authenticated:
                cart, created = MyCart.objects.get_or_create(user=request.user)
            else:
                session_key = request.session.session_key or request.session.create()
                cart, created = MyCart.objects.get_or_create(session_key=session_key)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                size=size,
                color=color,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            # ===== send server-side AddToCart event (CAPI) =====
            user_em = [request.user.email] if request.user.is_authenticated and getattr(request.user, 'email', None) else []
            user_ph = [getattr(request.user, 'phone_number', '')] if request.user.is_authenticated else []
            user_fullname = [getattr(request.user, 'fullname', '')] if request.user.is_authenticated else []

            event_id = send_event(
                event_name="AddToCart",
                user_data={
                    "em": user_em,
                    "ph": user_ph,
                    "fn": user_fullname,  # use fullname
                    "client_ip_address": get_client_ip(request),
                    "client_user_agent": request.META.get("HTTP_USER_AGENT"),
                },
                custom_data={
                    "content_ids": [product.product_code],
                    "content_name": product.product_name,
                    "currency": "BDT",
                    "value": float(product.discounted_price()) * quantity,
                    "quantity": quantity,
                }
            )
            # ====================================================

            return JsonResponse({
                "status": "success",
                "message": "Item added to cart!",
                "cart_count": cart.total_items(),
                "cart_total": str(cart.total_price()),
                "item": cart_item.to_dict(),
                "event_id": event_id,
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def get_cart_count(request):
    if request.user.is_authenticated:
        cart, created = MyCart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = MyCart.objects.get_or_create(session_key=session_key)

    return JsonResponse({"cart_count": cart.total_items()})
@csrf_exempt
def update_cart(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = data.get('quantity')
            
            # Add better validation
            if not item_id or item_id == "undefined":
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid item ID'
                }, status=400)
                
            try:
                item_id = int(item_id)
                quantity = int(quantity)
            except (ValueError, TypeError):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid ID or quantity format'
                }, status=400)
            
            cart_item = CartItem.objects.get(id=item_id)
            cart_item.quantity = quantity
            cart_item.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Quantity updated successfully',
                'new_quantity': quantity
            })
            
        except CartItem.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Cart item not found'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)
@csrf_exempt
def remove_from_cart(request):
    if request.method == "POST":
        data = json.loads(request.body)
        item_id = data.get("item_id")

        if not item_id:
            return JsonResponse({"status": "error", "message": "Item ID is missing."}, status=400)

        try:
            cart_item = get_object_or_404(CartItem, id=item_id)
            cart = cart_item.cart
            cart_item.delete()

            return JsonResponse({
                "status": "success",
                "message": "Item removed!",
                "cart_count": cart.total_items(),
                "cart_total": cart.total_price()
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def CartView(request):
    cart = None
    cart_items = []
    cart_total = 0

    if request.user.is_authenticated:
        cart, created = MyCart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key or request.session.create()
        cart, created = MyCart.objects.get_or_create(session_key=session_key)

    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    cart_total = sum(item.total_price() for item in cart_items)

    cart_items_data = []
    for item in cart_items:
        # Get the correct image URL based on color selection
        image_url = item.display_image  # This uses the display_image property
        absolute_image_url = request.build_absolute_uri(image_url) if image_url else ""

        cart_items_data.append({
            "id": item.id,
            "product_id": item.product.id,
            "product_image": absolute_image_url,
            "product_name": item.product.product_name,
            "product_price": str(item.product.discounted_price()),
            "quantity": item.quantity,
            "product_size": item.size,
            "product_color": item.color,
            #"product_type": item.product.product_type,
        })

    return JsonResponse({
        "cart_items": cart_items_data,
        "cart_total": cart_total,
    })

@csrf_exempt
def buy_now(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            quantity = int(data.get("quantity", 1))
            size = data.get("size", None)
            color = data.get("color", None)

            product = get_object_or_404(OurProduct, id=product_id)

            if request.user.is_authenticated:
                cart, created = MyCart.objects.get_or_create(user=request.user)
            else:
                session_key = request.session.session_key or request.session.create()
                cart, created = MyCart.objects.get_or_create(session_key=session_key)

            # Clear existing items for buy now functionality
            cart.items.all().delete()

            # Create new cart item with selected attributes
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
                size=size,
                color=color
            )

            # ===== Server-side Pixel Tracking =====
            user_em = [request.user.email] if request.user.is_authenticated and getattr(request.user, 'email', None) else []
            user_ph = [getattr(request.user, 'phone_number', '')] if request.user.is_authenticated else []
            user_fullname = [getattr(request.user, 'fullname', '')] if request.user.is_authenticated else []

            user_data = {
                "em": user_em,
                "ph": user_ph,
                "fn": user_fullname,
                "client_ip_address": get_client_ip(request),
                "client_user_agent": request.META.get("HTTP_USER_AGENT"),
            }

            # AddToCart event
            send_event(
                event_name="AddToCart",
                user_data=user_data,
                custom_data={
                    "content_ids": [product.product_code],
                    "content_name": product.product_name,
                    "currency": "BDT",
                    "value": float(product.discounted_price()) * quantity,
                    "quantity": quantity,
                }
            )

            # InitiateCheckout event
            send_event(
                event_name="InitiateCheckout",
                user_data=user_data,
                custom_data={
                    "content_ids": [product.product_code],
                    "content_name": product.product_name,
                    "currency": "BDT",
                    "value": float(product.discounted_price()) * quantity,
                    "quantity": quantity,
                }
            )
            # =====================================

            return JsonResponse({
                "status": "success",
                "redirect_url": "/checkout/",
                "item": {  
                    "id": cart_item.id,
                    "product_id": product.id,
                    "product_image": request.build_absolute_uri(cart_item.display_image),
                    "product_name": product.product_name,
                    "product_price": str(product.discounted_price()),
                    "quantity": quantity,
                    "product_size": size,
                    "product_color": color,
                }
            })
        except Exception as e:
            return JsonResponse({
                "status": "error", 
                "message": str(e)
            }, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def checkout_view(request):
    # 1. Cart Handling
    if request.user.is_authenticated:
        cart = MyCart.objects.get_or_create(user=request.user)[0]
    else:
        session_key = request.session.session_key or request.session.create()
        cart = MyCart.objects.get_or_create(session_key=session_key)[0]

    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    if not cart_items.exists():
        return redirect('user:home')

    # 2. Shipping Info Retrieval
    shipping_info = None
    if request.user.is_authenticated:
        shipping_info = ShippingInformation.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at').first()
    else:
        guest_phone = get_guest_phone_from_cookie(request)
        if guest_phone:
            shipping_info = ShippingInformation.objects.filter(
                phone=guest_phone,
                user__isnull=True,
                is_active=True
            ).order_by('-created_at').first()

    # 3. Form Submission Handling
    if request.method == 'POST':
        # Check if it's an AJAX validation request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'phone' in request.POST:
            phone = normalize_phone(request.POST.get("phone", ""))
            response_data = {'valid': True, 'message': ''}
            
            if not phone or len(phone) != 11:
                response_data = {
                    'valid': False, 
                    'message': 'Valid 11-digit phone number is required.'
                }
            else:
                valid_operator_codes = ('013', '014', '015', '016', '017', '018', '019')
                if not phone.startswith(valid_operator_codes):
                    response_data = {
                        'valid': False, 
                        'message': 'Invalid phone number. Must start with 013-019.'
                    }
            
            return JsonResponse(response_data)
        
        # Regular form submission handling
        phone = normalize_phone(request.POST.get("phone", ""))
        if not phone or len(phone) != 11:
            messages.error(request, 'Valid 11-digit phone number is required.')
            return redirect('product:checkout')

        form_data = {
            'full_name': request.POST.get("full_name", "").strip(),
            'email': request.POST.get("email", "").strip(),
            'phone': phone,
            'city': request.POST.get("city", "Dhaka").strip(),
            'address': request.POST.get("address", "").strip(),
            'special_note': request.POST.get("special_note", "").strip(),
            'delivery_location': (
                "inside_dhaka" if request.POST.get("delivery_location") == "70" 
                else "outside_dhaka"
            ),
        }

        # Validation
        try:
            validate_email(form_data['email'])
        except ValidationError:
            messages.error(request, "Invalid email address.")
            return redirect('product:checkout')

        valid_operator_codes = ('013', '014', '015', '016', '017', '018', '019')
        if not phone.startswith(valid_operator_codes):
            messages.error(request, 'Invalid phone number. Must start with 013-019.')
            return redirect('product:checkout')

        # Handle shipping info creation/update
        try:
            if request.user.is_authenticated:
                shipping_info, created = ShippingInformation.objects.update_or_create(
                    user=request.user,
                    phone=phone,
                    defaults={**form_data, 'is_active': True}
                )
            else:
                shipping_info, created = ShippingInformation.objects.update_or_create(
                    phone=phone,
                    user=None,
                    defaults={**form_data, 'is_active': True}
                )
                
            ShippingInformation.objects.filter(
                user=request.user if request.user.is_authenticated else None,
                phone=phone
            ).exclude(pk=shipping_info.pk).update(is_active=False)

        except Exception as e:
            messages.error(request, "Error saving shipping information. Please try again.")
            logger.error(f"Shipping info save error: {str(e)}")
            return redirect('product:checkout')

        # Create temporary order for verification
        verification_code = str(random.randint(100000, 999999))
        try:
            order = Order.objects.create(
                shipping_info=shipping_info,
                verification_code=verification_code,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key if not request.user.is_authenticated else None,
                delivery_cost=shipping_info.get_delivery_cost
            )
        except Exception as e:
            messages.error(request, "Order creation failed. Please try again.")
            logger.error(f"Order creation error: {str(e)}")
            return redirect('product:checkout')

        # Verification Setup
        request.session.update({
            'verification_code': verification_code,
            'order_id': order.id,
            'verification_attempts': 0,
            'last_sms_time': time.time(),
            'phone_number': phone,
            'cart_id': cart.id,
            'shipping_info_id': shipping_info.id
        })

        # Send verification code
        if not send_verification_code(request, phone, form_data['email'], verification_code):
            return redirect('product:checkout')
        # 🔹 SEND FACEBOOK EVENT (InitiateCheckout)
        try:
            user_fullname = [getattr(request.user, 'fullname', '')] if request.user.is_authenticated else []

            raw_user_data = {
                "em": [form_data.get('email')] if form_data.get('email') else [],
                "ph": [phone] if phone else [],
                "fn": user_fullname,
                "client_user_agent": request.META.get("HTTP_USER_AGENT"),
                "client_ip_address": get_client_ip(request),  # Use helper to get real IP
            }

            user_data = normalize_user_data(raw_user_data)

            custom_data = {
                "currency": "BDT",
                "value": sum(item.total_price() for item in cart_items),
                "contents": [
                    {"id": str(item.product.id), "quantity": item.quantity}
                    for item in cart_items
                ],
                "content_type": "product",
            }

            event_id = send_event(
                event_name="InitiateCheckout",
                user_data=user_data,
                custom_data=custom_data
            )
            logger.info(f"InitiateCheckout Pixel Event sent with event_id={event_id}")

        except Exception as e:
            logger.error(f"Pixel event send error: {str(e)}")
        # Clear messages and set cookie
        list(messages.get_messages(request))
        response = redirect('product:verify_email')
        
        if not request.user.is_authenticated:
            response.set_cookie(
                'guest_phone',
                Signer().sign(phone),
                max_age=60*60*24*90,
                secure=not settings.DEBUG,
                httponly=True,
                samesite='Lax'
            )
        return response

    # Prepare form data
    initial_data = {}
    if shipping_info:
        initial_data = {
            'full_name': shipping_info.full_name,
            'email': shipping_info.email,
            'phone': shipping_info.phone,
            'city': shipping_info.city,
            'address': shipping_info.address,
            'special_note': shipping_info.special_note or '',
            'delivery_location': shipping_info.delivery_location,
        }

    cart_items_data = []
    for item in cart_items:
        # Get the correct image based on selected color
        if item.color:
            color_image = item.product.images.filter(color__name__iexact=item.color).first()
            product_image = color_image.image if color_image else item.product.product_image
        else:
            product_image = item.product.product_image

        cart_items_data.append({
            "product_image": product_image,
            "product_name": item.product.product_name,
            "product_price": item.product.discounted_price(),
            "quantity": item.quantity,
            "id": item.id,
            "product_id": item.product.id,
            "product_size": item.size,
            "product_color": item.color,
        })


    context = {
        "cart_items": cart_items_data,
        "cart_total": sum(item.total_price() for item in cart_items),
        "shipping_form": ShippingInformationForm(initial=initial_data),
    }
    return render(request, "product/checkout.html", context)

def send_verification_code(request, phone, email, verification_code):
    """Trigger Celery task to send verification code"""
    try:
        # Run the task asynchronously
        send_verification_code_task.delay(phone, email, verification_code)
        
        # Store verification attempt
        request.session['verification_code'] = verification_code
        request.session['last_sms_time'] = time.time()
        request.session['delivery_method'] = 'sms'  # Assume SMS will work
        
        messages.success(request, 'Verification code sent to your phone number.')
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification code: {str(e)}")
        messages.error(request, 'Failed to send verification code. Please try again.')
        return False

def verify_email_view(request):
    if not request.session.get('verification_code'):
        messages.error(request, 'No verification session found. Please start checkout again.')
        return redirect('product:checkout')
    
    if request.method == 'POST':
        if 'resend_code' in request.POST:
            storage = messages.get_messages(request)
            storage.used = True
            
            current_time = time.time()
            last_sms_time = request.session.get('last_sms_time', 0)
            
            if current_time - last_sms_time < 60:
                remaining_time = int(60 - (current_time - last_sms_time))
                messages.error(request, f'Please wait {remaining_time} seconds before requesting a new code.')
            else:
                verification_code = str(random.randint(100000, 999999))
                request.session['verification_code'] = verification_code
                request.session['verification_attempts'] = 0
                
                phone = request.session.get('phone_number')
                shipping_info = get_object_or_404(
                    ShippingInformation, 
                    id=request.session['shipping_info_id']
                )
                
                # Update order with new verification code
                order = get_object_or_404(Order, id=request.session['order_id'])
                order.verification_code = verification_code
                order.save()
                
                if send_verification_code(request, phone, shipping_info.email, verification_code):
                    method = request.session.get('delivery_method', 'sms')
                    messages.success(request, f'New verification code sent to your {method}!')
                else:
                    messages.error(request, 'Failed to resend code. Please try again.')
            
            return redirect('product:verify_email')
        
        entered_code = request.POST.get('verification_code')
        stored_code = str(request.session.get('verification_code'))
        
        if entered_code == stored_code:
            return process_successful_verification(request)
        else:
            attempts = request.session.get('verification_attempts', 0) + 1
            request.session['verification_attempts'] = attempts
            
            if attempts >= 3:
                messages.error(request, 'Too many failed attempts. Please start checkout again.')
                clear_verification_session(request)
                return redirect('product:checkout')
            else:
                messages.error(request, f'Invalid verification code. {3 - attempts} attempts remaining.')
                return redirect('product:verify_email')
    
    current_time = time.time()
    last_sms_time = request.session.get('last_sms_time', 0)
    cooldown_remaining = max(0, 60 - (current_time - last_sms_time))
    
    context = {
        'cooldown_remaining': int(cooldown_remaining),
        'email': ShippingInformation.objects.get(
            id=request.session['shipping_info_id']
        ).email if request.session.get('shipping_info_id') else None,
        'phone': request.session.get('phone_number'),
        'delivery_method': request.session.get('delivery_method', 'sms')
    }
    return render(request, 'product/verify_email.html', context)

def process_successful_verification(request):
    """Complete the order after successful verification"""
    try:
        with transaction.atomic():
            # Get the temporary order
            order = get_object_or_404(Order, id=request.session['order_id'])
            cart = get_object_or_404(MyCart, id=request.session['cart_id'])
            cart_items = CartItem.objects.filter(cart=cart)
            
            if not cart_items.exists():
                raise Exception("Cart is empty")
            
            # Calculate totals
            subtotal = sum(item.total_price() for item in cart_items)
            delivery_cost = order.delivery_cost
            grand_total = subtotal + delivery_cost
            
            # Update order with final details (DON'T change status here)
            order.total_price = subtotal
            order.grand_total = grand_total
            order.is_verified = True  # Only mark as verified
            order.save()  # Status remains 'pending' by default
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.discounted_price(),
                    size=item.size,
                    color=item.color
                )
            
            # Clear cart
            cart_items.delete()
            
            # Clear session
            clear_verification_session(request)
            
            return redirect('product:order_confirmation', order_id=order.order_id)
            
    except Exception as e:
        logger.error(f"Order completion error: {str(e)}")
        messages.error(request, 'Error completing your order. Please try again.')
        clear_verification_session(request)
        return redirect('product:checkout')

def clear_verification_session(request):
    """Clear verification-related session data"""
    keys = [
        'verification_code', 'order_id', 'verification_attempts',
        'last_sms_time', 'phone_number', 'delivery_method', 'cart_id',
        'shipping_info_id'
    ]
    for key in keys:
        if key in request.session:
            del request.session[key]
    request.session.modified = True


def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    order_items = OrderItem.objects.filter(order=order).select_related('product')

    order_items_data = []
    for item in order_items:
        order_items_data.append({
            'product': item.product,
            'quantity': item.quantity,
            'price': item.price,
            'size': item.size,
            'color': item.color,
            'image': item.display_image,
            'total': item.price * item.quantity
        })

    total_quantity = sum(item.quantity for item in order_items)
    # 🔹 SERVER-SIDE PIXEL: Purchase
    total_value = sum(float(item.price) * item.quantity for item in order_items)

    # Safe email/phone
    user_email = getattr(order.shipping_info, 'email', None)
    user_phone = getattr(order.shipping_info, 'phone', None)
    user_fullname = [getattr(order.shipping_info, 'fullname', '')] if getattr(order.shipping_info, 'fullname', None) else []

    event_id = send_event(
        event_name="Purchase",
        user_data={
            "em": [user_email] if user_email else [],
            "ph": [user_phone] if user_phone else [],
            "fn": user_fullname,
            "client_user_agent": request.META.get("HTTP_USER_AGENT"),
            "client_ip_address": get_client_ip(request),
        },
        custom_data={
            "currency": "BDT",
            "value": total_value,
            "contents": [
                {
                    "id": item.product.product_code,
                    "quantity": item.quantity,
                    "item_price": float(item.price)
                }
                for item in order_items
            ],
            "content_type": "product",
        }
    )

    logger.info(f"Purchase Pixel Event sent with event_id={event_id}")


    context = {
        'order': order,
        'order_items': order_items_data,
        'total_quantity': total_quantity,
        'shipping_info': order.shipping_info,
        'event_id': event_id,
        'total_value': total_value, 
    }
    return render(request, 'product/order_confirmation.html', context)


@require_GET
def search_view(request):
    """AJAX search for autocomplete suggestions"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if len(query) < 2:
        return JsonResponse({'error': 'Query too short'}, status=400)
    
    try:
        # Search products
        products = OurProduct.objects.filter(
            Q(product_name__icontains=query) |
            Q(product_code__icontains=query) |
            Q(product_details__icontains=query)
        ).values('product_name', 'product_slug')[:5]
        
        for p in products:
            results.append({
                'name': p['product_name'],
                'slug': p['product_slug'],
                'model': 'ourproduct',
                'url': f"/product-details/{p['product_slug']}/"
            })
        
        # Search brands - FIXED: Use objects directly instead of values()
        brands = ProductBrand.objects.filter(
            Q(title__icontains=query)
        )[:3]
        
        for b in brands:
            results.append({
                'name': b.title,
                'slug': b.slug,
                'model': 'productbrand',
                'url': f"/brand-products/{b.slug}/" 
            })
        
        # Search categories
        categories = FeatureCategory.objects.filter(
            title__icontains=query
        ).values('title', 'slug')[:3]
        
        for c in categories:
            results.append({
                'name': c['title'],
                'slug': c['slug'],
                'model': 'featurecategory',
                'url': f"/category-products/{c['slug']}/"
            })
        
        # Search subcategories
        subcategories = ProductSubcategory.objects.filter(
            title__icontains=query
        )[:3]

        for s in subcategories:
            url = f"/subcategory-products/{s.slug}/"
            
            results.append({
                'name': s.title,
                'slug': s.slug,
                'model': 'productsubcategory',
                'url': url
            })
                
        # Search ProductMoreSubCategory - NEW
        more_subcategories = ProductMoreSubCategory.objects.filter(
            Q(title__icontains=query)
        )[:3]
        
        for msc in more_subcategories:
            # For ProductMoreSubCategory, we know it has a category field
            parent_slug = msc.category.slug if msc.category else None
            
            if parent_slug:
                url = f"/products/{parent_slug}/{msc.slug}/"
            else:
                url = "#"
                
            results.append({
                'name': msc.title,
                'slug': msc.slug,
                'model': 'productmoresubcategory',
                'url': url
            })
        
        return JsonResponse(results, safe=False)
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)

@require_GET
def search_results_view(request):
    """Full search results page - only shows when no suggestions found"""
    query = request.GET.get('q', '').strip()
    
    context = {
        "query": query,
        "has_results": False 
    }
    return render(request, "product/search_results.html", context)

def ContactUsView(request):
    form = ContactWithUsForm()
    if request.method == 'POST':
        form = ContactWithUsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message sent successfully.")
            return redirect('product:contact')    
    return render(request, 'product/contact.html', context={'form':form})

@csrf_exempt
@require_POST
def apply_promo_code(request):
    code = request.POST.get('code', '').strip()
    
    if not code:
        return JsonResponse({
            'success': False,
            'message': 'Please enter a promo code'
        })

    try:
        promo = PromoCode.objects.get(code=code, is_active=True)
        
        # Custom validation method - ensure this exists in your PromoCode model
        if hasattr(promo, 'is_valid') and not promo.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Promo code is not valid'
            })
        
        # Prepare promo data structure
        promo_data = {
            'code': promo.code,
            'discount_type': promo.discount_type,
            'discount_value': float(promo.discount_value)
        }
        
        # Store in appropriate session key
        session_key = 'promo_code' if request.user.is_authenticated else 'guest_promo_code'
        request.session[session_key] = promo_data
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': 'Promo code applied successfully!',
            'promo_data': promo_data
        })
        
    except PromoCode.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Invalid promo code'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while applying the promo code'
        })

@csrf_exempt
@require_POST
def remove_promo_code(request):
    try:
        # Clear promo code for both guest and logged-in users
        session_keys = ['promo_code', 'guest_promo_code']
        for key in session_keys:
            if key in request.session:
                del request.session[key]
        
        request.session.modified = True
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Failed to remove promo code'
        })
    
@require_POST
@login_required
def toggle_wishlist(request):
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Product ID is required'
            }, status=400)
            
        
        product = OurProduct.objects.get(id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        if product in wishlist.products.all():
            wishlist.products.remove(product)
            action = 'removed'
        else:
            wishlist.products.add(product)
            action = 'added'
            
        return JsonResponse({
            'status': 'success',
            'action': action,
            'wishlist_count': wishlist.products.count()
        })
        
    except OurProduct.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Product not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    
@login_required
def WishlistView(request):
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        products = wishlist.products.all()
    except Wishlist.DoesNotExist:
        products = []  # or None, if you prefer

    return render(request, 'product/wishlist_product.html', context={'products': products})

@require_POST
@csrf_exempt
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def update_order_status(request, order_id):
    try:
        import json
        data = json.loads(request.body)
        new_status = data.get('status')
        
        order = Order.objects.get(id=order_id)
        
        if new_status in dict(Order._meta.get_field('status').choices):
            order.status = new_status
            order.save()
            return JsonResponse({'success': True})
            
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def order_dashboard(request):
    orders = Order.objects.all().order_by('-created_at')

    # --- Verified filter ---
    verified_filter = request.GET.get('verified', 'all') 
    if verified_filter == 'true':
        orders = orders.filter(is_verified=True)
    elif verified_filter == 'false':
        orders = orders.filter(is_verified=False)

    # --- Status filter ---
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)

    # --- Search filter ---
    search_query = request.GET.get('search', '').strip()
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(shipping_info__full_name__icontains=search_query) |
            Q(shipping_info__phone__icontains=search_query) |
            Q(shipping_info__email__icontains=search_query)
        )

    # --- Date filters ---
    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=date_from)
        except ValueError:
            pass

    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    # --- Pagination ---
    paginator = Paginator(orders, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- AJAX response ---
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'orders': [{
                'id': order.id,
                'order_id': order.order_id,
                'created_at': order.created_at.strftime("%b %d, %Y %I:%M %p"),
                'customer_name': order.shipping_info.full_name,
                'customer_phone': order.shipping_info.phone,
                'customer_email': order.shipping_info.email,
                'customer_address': f"{order.shipping_info.address}, {order.shipping_info.city}",
                'products_list': ', '.join([item.product.product_name for item in order.order_items.all()]),
                'total_quantity': order.order_items.aggregate(total=Sum('quantity'))['total'] or 0,
                'total_price': float(order.total_price),
                'has_discount': order.discount_amount > 0,
                'discount_amount': float(order.discount_amount),
                'promo_code_used': order.promo_code_used,
                'delivery_cost': float(order.delivery_cost),
                'grand_total': float(order.grand_total),
                'status': order.status,
                'status_options': [choice[0] for choice in Order._meta.get_field('status').choices],
                'order_url': reverse('product:order_confirmation', args=[order.order_id]),
                'is_verified': order.is_verified,
            } for order in page_obj],
            'has_next': page_obj.has_next()
        }
        return JsonResponse(data)

    return render(request, 'dashboard/order_dashboard.html')

def schedule_message_view(request):
    if request.method == "POST":
        form = ScheduledMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Message scheduled successfully!")
            return redirect("product:order_dashboard")
    else:
        form = ScheduledMessageForm()
    return render(request, "product/schedule_message.html", {"form": form})

def brand_products_view(request, brand_slug):
    brand = get_object_or_404(ProductBrand, slug=brand_slug)
    products = OurProduct.objects.filter(product_brand=brand)
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON with HTML content
        html = render_to_string('product/product_list_ajax.html', {'products': page_obj})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })
    
    context = {
        'brand': brand,
        'products': page_obj,
    }
    return render(request, 'product/brand_products.html', context)

def subcategory_products_view(request, subcategory_slug):
    """View to display products by subcategory"""
    subcategory = get_object_or_404(ProductSubcategory, slug=subcategory_slug)
    products = OurProduct.objects.filter(product_sub_category=subcategory)
    
    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON with HTML content
        html = render_to_string('product/product_list_ajax.html', {'products': page_obj})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })
    
    context = {
        'subcategory': subcategory,
        'products': page_obj,
    }
    return render(request, 'product/subcategory_products.html', context)


#############
#Facebook product Feed
from django.utils.html import escape
from django.contrib.sites.models import Site
def facebook_product_feed(request):
    products = OurProduct.objects.filter(product_status=True)
    current_site = Site.objects.get_current()
    domain = f"https://{current_site.domain}"

    xml_data = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_data += '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n'
    xml_data += '<channel>\n'
    xml_data += '<title>Your Shop Product Feed</title>\n'

    for p in products:
        xml_data += "<item>\n"
        xml_data += f"<g:id>{escape(p.product_code)}</g:id>\n"
        xml_data += f"<title>{escape(p.product_name)}</title>\n"
        xml_data += f"<description>{escape(p.product_details[:500])}</description>\n"
        xml_data += f"<link>{domain}/product-details/{p.product_slug}/</link>\n"
        xml_data += f"<g:image_link>{domain}{p.product_image.url}</g:image_link>\n"
        xml_data += f"<g:price>{p.product_price} BDT</g:price>\n"
        xml_data += f"<g:availability>in stock</g:availability>\n"
        xml_data += f"<g:condition>new</g:condition>\n"

        # Category
        if p.product_category:
            xml_data += f"<g:product_type>{escape(p.product_category.title)}</g:product_type>\n"

        # Brand
        if p.product_brand:
            xml_data += f"<g:brand>{escape(p.product_brand.title)}</g:brand>\n"

        # SKU / Unique Code
        xml_data += f"<g:sku>{escape(p.product_code)}</g:sku>\n"

        xml_data += "</item>\n"

    xml_data += "</channel>\n</rss>"

    return HttpResponse(xml_data, content_type="application/xml")