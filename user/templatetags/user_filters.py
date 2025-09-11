from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def format_view_count(value):
    """
    Format view count to abbreviated form (e.g., 1000 -> 1K, 1500 -> 1.5K)
    """
    try:
        value = int(value)
        if value >= 1000000:
            result = f"{value/1000000:.1f}M".replace('.0', '')
        elif value >= 1000:
            result = f"{value/1000:.1f}K".replace('.0', '')
        else:
            result = str(value)
        return mark_safe(result)
    except (ValueError, TypeError):
        return value

@register.filter
def format_view_count_icon(value):
    """
    Format view count with eye icon
    """
    try:
        value = int(value)
        if value >= 1000000:
            result = f"{value/1000000:.1f}M".replace('.0', '')
        elif value >= 1000:
            result = f"{value/1000:.1f}K".replace('.0', '')
        else:
            result = str(value)
        return mark_safe(f'<i class="bi bi-eye-fill"></i> {result}')
    except (ValueError, TypeError):
        return mark_safe(f'<i class="bi bi-eye-fill"></i> {value}')