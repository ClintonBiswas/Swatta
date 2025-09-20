# user/context_processors.py
from django.conf import settings
from product.models import ProductMoreSubCategory, FeatureCategory

def global_subcategories(request):
    context = {}
    
    # Define the mapping between category slugs and template variable names
    category_mapping = {
        'men-fashion': 'mens_fashion_subcategories',
        'women-fashion': 'womens_fashion_subcategories',
        'kids': 'kids_item_subcategories',
        'gadgets': 'gadgets_subcategories',
        'accessories': 'accessories_subcategories',
        'food': 'food_subcategories'
    }

    # Get all categories that we want to display
    categories = FeatureCategory.objects.filter(slug__in=category_mapping.keys())
    
    for category in categories:
        subcategories = ProductMoreSubCategory.objects.filter(category=category)
        context[category_mapping[category.slug]] = subcategories

    return context

def facebook_pixel(request):
    return {
        'FACEBOOK_PIXEL_ID': settings.FACEBOOK_PIXEL_ID
    }


