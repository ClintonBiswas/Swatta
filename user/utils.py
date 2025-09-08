from datetime import timedelta
from django.core.cache import cache
from product.models import OurProduct
from django.utils import timezone
from django.db.models import (
    Count, 
    Q, 
)

def get_popular_products(limit=20, days=30, category=None):
    cache_key = f'popular_products_{limit}_{days}_{category.pk if category else "all"}'
    result = cache.get(cache_key)

    if result is None:
        cutoff = timezone.now() - timedelta(days=days)
        qs = OurProduct.objects.all()

        if category:
            qs = qs.filter(product_category=category)

        result = list(
            qs.filter(product_views__timestamp__gte=cutoff)
              .annotate(recent_views=Count('product_views'))
              .order_by('-recent_views', '-view_count')[:limit]
        )

        if len(result) < limit:
            remaining = limit - len(result)
            additional = list(
                qs.exclude(pk__in=[p.pk for p in result])
                  .order_by('-view_count')[:remaining]
            )
            result.extend(additional)

        cache.set(cache_key, result, 3600)

    return result
