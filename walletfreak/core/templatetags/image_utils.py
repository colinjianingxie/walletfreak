from django import template
from django.templatetags.static import static
import os
from django.conf import settings

register = template.Library()

@register.simple_tag
def get_card_image_url(card_slug):
    """
    Returns the URL for a card image, checking various extensions.
    """
    if not card_slug:
        return static('images/card_placeholder.png') # Make sure you have a placeholder or handle this
        
    extensions = ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG', '.webp', '.WEBP', '.avif', '.AVIF']
    
    # Check if we can find the file in the generated static files (collected) or source
    # For dev, we usually look in the source static folders. 
    # This is a bit tricky depending on static setup, but checking file existence is safest if we know the path.
    # Assuming standard structure: static/images/credit_cards/
    
    # We'll just return the static path and let the browser try? No, that's inefficient/404s.
    # We should detect which one exists.
    
    # Try to find the file in the static directory
    static_card_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'credit_cards')
    
    for ext in extensions:
        filename = f"{card_slug}{ext}"
        if os.path.exists(os.path.join(static_card_dir, filename)):
            return static(f"images/credit_cards/{filename}")
            
    # Fallback
    return static('images/card_placeholder.png')
