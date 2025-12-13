from django import template
from django.templatetags.static import static
from django.conf import settings
import os

register = template.Library()

def resolve_card_image_url(card_slug):
    """
    Helper function to resolve card image URL.
    Can be imported by views.
    """
    if not card_slug:
        return static('images/card_placeholder.png') # Ensure you have this or handle it
        
    extensions = ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG', '.webp', '.WEBP', '.avif', '.AVIF']
    static_card_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'credit_cards')
    
    for ext in extensions:
        filename = f"{card_slug}{ext}"
        if os.path.exists(os.path.join(static_card_dir, filename)):
            return static(f"images/credit_cards/{filename}")
            
    # Fallback to a default placeholder if specific card image not found
    return static('images/card_placeholder.png')

@register.simple_tag
def get_card_image_url(card_slug):
    """
    Template tag to get card image URL.
    """
    return resolve_card_image_url(card_slug)

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
