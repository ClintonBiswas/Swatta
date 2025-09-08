from django import template

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """Multiplies the value by the argument."""
    return value * arg

@register.filter(name='mula')
def mula(value, arg):
    """Multiplies the given value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0  # Return 0 if invalid values

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0