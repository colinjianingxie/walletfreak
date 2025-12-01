from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if dictionary is None:
        return None
    return dictionary.get(key, 0)

@register.filter
def strip(value):
    """Strip whitespace from a string"""
    if hasattr(value, 'strip'):
        return value.strip()
    return value
