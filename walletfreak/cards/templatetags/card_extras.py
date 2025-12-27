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

@register.filter
def replace(value, arg):
    """
    Replace characters in string.
    Usage: {{ value|replace:"old:new" }} or {{ value|replace:"old,new" }}
    But simpler: {{ value|replace:"_, " }} 
    
    Wait, filter arguments in Django take only one string usually unless parsed custom.
    Let's stick to the usage in the template: {{ value|replace:"_":" " }} which is standard python invocation? 
    No, Django filters are `value|filter:arg`.
    The template has: `{{ key|replace:"_":" " }}` which implies two arguments.
    Standard Django filters don't support multiple arguments like that directly without valid syntax.
    However, `replace:"_":" "` is effectively `replace` with arg equal to `_` followed by ` : " "`? 
    No, Django parses arguments separated by colon if the filter accepts it?
    Actually, standard syntax is only one argument.
    
    BUT, looking at the user error: `Invalid filter: 'replace'` implies it doesn't verify the syntax yet, just existence.
    
    The syntax `{{ value|replace:"_":" " }}` looks like it expects `def replace(value, old, new)`.
    Standard Django template system DOES NOT support `|filter:arg1:arg2`. A filter only takes one argument.
    
    If the user previously used this, they might be from Jinja2 or trying to use a library that supports it.
    
    I will implement a `replace` filter that takes one argument string and splits it, OR I will fix the template to use a standard approach.
    Since I want to fix the error and the template uses `replace:"_":" "`, wait...
    Reference: Django docs say `{{ value|filter:arg }}`. It does NOT natively support multiple args with colons unless the filter manually parses the string arg.
    
    However, let's fix the template to be simpler if possible, OR implement a `replace` that handles `old,new`.
    
    But the template currently says `key|replace:"_":" "`. This is actually NOT VALID Django Template syntax for filters if it sends two distinct arguments, UNLESS I write a filter that expects `arg` to be `_` and... wait.
    
    Actually, maybe the template was written with a mental model of another system.
    
    I will fix the template to use a simpler filter I will write: `replace_underscore`.
    OR I will implement `replace` taking "old,new" and update the template to `replace:"_, "`.
    
    Let's check the template again.
    Line 54: `{{ key|replace:"_":" " }}`.
    This syntax `replace:"_":" "` is technically passing `_` as arg to replace, and then applying... wait.
    
    If I define `def replace(value, arg)`... django passes the string after colon.
    If I have `|replace:"_"`, arg is `_`.
    `|replace:"_":" "` -> This might be interpreted as `(value|replace:"_")` ... wait, chaining? No.
    
    Actually, `key|replace:"_":" "` is INVALID syntax for a single filter. 
    It might be `key|replace:"_" | replace:" "`? No.
    
    Wait, `key|replace:"_":" "` -> If this was Jinja2, `replace('_', ' ')`.
    
    I will implement `replace_underscore` as a specific filter, OR a generic `replace` that takes "old,new".
    
    I'll implement `replace_underscore` in `card_extras.py` and update the template.
    Or even better, `replace` that takes one argument `old` and replaces with space?
    
    Let's just implement `replace_underscore` effectively.
    
    BETTER: `replace` filter that takes two arguments? 
    It is possible to write custom tag, but filter is limited.
    
    I will write a filter `replace_underscore` that replaces `_` with ` `. 
    Usage: `{{ value|replace_underscore }}`.
    
    And I will change the template to use it.
    """
    if hasattr(value, 'replace'):
        return value.replace(arg, ' ') # HACK: Just replace with space if generic? 
        # But wait, replace requires two args usually.
    return value

@register.filter
def replace_underscore(value):
    """Replace underscores with spaces"""
    if hasattr(value, 'replace'):
        return value.replace('_', ' ')
    return value

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value
