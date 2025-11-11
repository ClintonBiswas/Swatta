from django.shortcuts import render, get_object_or_404
from django.urls import reverse, NoReverseMatch
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json, time, logging
from .models import Poll, PollOption, Vote
from product.models import PromoCode, FeatureCategory
from django.utils import timezone
from user.utils import get_popular_products
from product.utils import send_event
from .utils import get_client_ip

logger = logging.getLogger(__name__)
def poll_list(request):
    polls = Poll.objects.filter(is_active=True).order_by('-created_at')
    category = FeatureCategory.objects.filter(poll__is_active=True).first()
    products = get_popular_products(limit=10, days=30, category=category)
    promo_code = PromoCode.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now()
    ).first()
    context = {
        'polls': polls,
        'promo_code': promo_code,
        'products' : products
    }
    return render(request, 'polls/poll_list.html', context)

@csrf_protect
@require_POST
def ajax_vote(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        poll_id = data.get('poll_id')
        option_ids = data.get('option_ids')

        if not poll_id or not option_ids:
            return JsonResponse({'error': 'Invalid request data'}, status=400)

        ip_address = get_client_ip(request)
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key

        poll = get_object_or_404(Poll, id=poll_id, is_active=True)

        # shop_now_url
        shop_now_url = reverse('user:home')
        if poll.product_category and poll.product_category.slug:
            try:
                shop_now_url = reverse('product:category-products', kwargs={'category_slug': poll.product_category.slug})
            except NoReverseMatch:
                shop_now_url = f'/category-products/{poll.product_category.slug}/'

        # --- Active promo code ---
        promo_code = PromoCode.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).first()

        promo_data = {}
        if promo_code and promo_code.is_valid():
            promo_data = {
                'promo_code': promo_code.code,
                'promo_message': f"Use code {promo_code.code} for {promo_code.get_discount_display()} off!",
                'discount': promo_code.get_discount_display(),
                'valid_until': promo_code.valid_to.strftime('%d %b %Y'),
                'shop_now_url': shop_now_url
            }

        # --- Normalize option_ids ---
        if not isinstance(option_ids, list):
            option_ids = [option_ids]

        if poll.poll_type == Poll.SINGLE and len(option_ids) > 1:
            return JsonResponse({'error': 'This poll only allows single choice'}, status=400)

        valid_options = set(poll.options.values_list('id', flat=True))
        if not all(option_id in valid_options for option_id in option_ids):
            return JsonResponse({'error': 'Invalid option selected'}, status=400)

        # --- Remove previous votes ---
        voter_filter = {'poll': poll}
        if request.user.is_authenticated:
            voter_filter['user'] = request.user
        else:
            voter_filter['session_key'] = session_key

        Vote.objects.filter(**voter_filter).delete()

        # --- Create new votes ---
        voted_options = []
        for option_id in option_ids:
            option = poll.options.get(id=option_id)
            Vote.objects.create(
                poll=poll,
                option=option,
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key if not request.user.is_authenticated else None,
                ip_address=ip_address,
            )
            voted_options.append(option.text or str(option.id))

        # --- Recalculate total votes ---
        poll.total_votes = Vote.objects.filter(poll=poll).values('user', 'session_key').distinct().count()
        poll.save()

        # -----------------------------
        # SERVER-SIDE PIXEL: PollVote
        # -----------------------------
        try:
            user_em = [request.user.email] if request.user.is_authenticated and getattr(request.user, 'email', None) else []
            user_ph = [getattr(request.user, 'phone_number', '')] if request.user.is_authenticated else []

            event_id = request.COOKIES.get("fb_event_id") or f"pollvote_{poll.id}_{int(time.time()*1000)}"
            ip_address = get_client_ip(request)  # make sure you have this utility

            send_event(
                event_name="PollVote",
                event_id=event_id,  # deduplication
                user_data={
                    "em": user_em,
                    "ph": user_ph,
                    "client_ip_address": ip_address,
                    "client_user_agent": request.META.get("HTTP_USER_AGENT"),
                    "fbc": [request.COOKIES.get("_fbc")] if request.COOKIES.get("_fbc") else [],
                    "fbp": [request.COOKIES.get("_fbp")] if request.COOKIES.get("_fbp") else [],
                },
                custom_data={
                    "poll_id": poll.id,
                    "option_ids": option_ids,
                    "option_texts": voted_options,
                    "total_votes": poll.total_votes,
                    "content_type": "poll",
                    "content_name": "Winter Collection Poll",     
                    "content_ids": [f"poll_{poll.id}"],           
                    "content_category": "Winter Collection",     
                    "event_source_url": request.build_absolute_uri(), 
                    "value": 1.0,                                 
                    "currency": "BDT",                            
                }
            )
        except Exception as e:
            logger.error(f"PollVote Pixel send error: {str(e)}")


        # --- Prepare results ---
        result_data = []
        for idx, option in enumerate(poll.options.all()):
            votes = option.vote_count
            percentage = (votes / poll.total_votes * 100) if poll.total_votes > 0 else 0
            result_data.append({
                'id': option.id,
                'text': option.text,
                'image_url': option.image.url if option.image else None,
                'votes': votes,
                'percentage': round(percentage, 2),
                'color': get_color_for_option(idx),
            })

        return JsonResponse({
            'success': True,
            'message': 'Your vote has been recorded!',
            'results': result_data,
            'total_votes': poll.total_votes,
            **promo_data  # <-- restore promo info
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except PollOption.DoesNotExist:
        return JsonResponse({'error': 'Invalid option selected'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def get_color_for_option(index):
    colors = [
        '#4285F4', '#EA4335', '#FBBC05', '#34A853', '#673AB7',
        '#FF5722', '#009688', '#795548', '#607D8B', '#9C27B0'
    ]
    return colors[index % len(colors)]
