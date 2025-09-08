# views.py
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json
from .models import Poll, PollOption, Vote
from product.models import PromoCode, OurProduct, FeatureCategory
from django.db.models import Q
from django.utils import timezone
from user.utils import get_popular_products

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

        # Active promo code
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
                'shop_now_url': reverse('user:home')
            }

        # Check if already voted
        existing_vote = Vote.objects.filter(
            Q(poll=poll, session_key=session_key) |
            Q(poll=poll, ip_address=ip_address) |
            (Q(poll=poll, user=request.user) if request.user.is_authenticated else Q(pk=None))
        ).exists()

        if existing_vote:
            poll.update_total_votes()  # ensure it's fresh
            poll.refresh_from_db()

            options = poll.options.all()
            result_data = []
            for idx, option in enumerate(options):
                result_data.append({
                    'id': option.id,
                    'text': option.text,
                    'image_url': option.image.url if option.image else None,
                    'votes': option.vote_count,
                    'percentage': option.percentage,
                    'color': get_color_for_option(idx)  # fixed color assignment
                })

            return JsonResponse({
                'already_voted': True,
                'message': 'You have already voted on this poll. Here are the current results:',
                'results': result_data,
                'total_votes': poll.total_votes,
                **promo_data
            })

        # Validate options
        if not isinstance(option_ids, list):
            option_ids = [option_ids]
        if poll.poll_type == Poll.SINGLE and len(option_ids) > 1:
            return JsonResponse({'error': 'This poll only allows single choice'}, status=400)

        valid_options = set(poll.options.values_list('id', flat=True))
        if not all(option_id in valid_options for option_id in option_ids):
            return JsonResponse({'error': 'Invalid option selected'}, status=400)

        # Create votes
        for option_id in option_ids:
            option = PollOption.objects.get(id=option_id, poll=poll)
            Vote.objects.create(
                poll=poll,
                option=option,
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key,
                ip_address=ip_address,
            )

        poll.update_total_votes()
        poll.refresh_from_db()

        options = poll.options.all()
        result_data = []
        for idx, option in enumerate(options):
            result_data.append({
                'id': option.id,
                'text': option.text,
                'image_url': option.image.url if option.image else None,
                'votes': option.vote_count,
                'percentage': option.percentage,
                'color': get_color_for_option(idx)
            })

        return JsonResponse({
            'success': True,
            'message': 'Vote recorded successfully!',
            'results': result_data,
            'total_votes': poll.total_votes,
            **promo_data
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except PollOption.DoesNotExist:
        return JsonResponse({'error': 'Invalid option selected'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def get_color_for_option(index):
    colors = [
        '#4285F4', '#EA4335', '#FBBC05', '#34A853', '#673AB7',
        '#FF5722', '#009688', '#795548', '#607D8B', '#9C27B0'
    ]
    return colors[index % len(colors)]
