from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Replaces GET parameters in the current URL with the provided keyword arguments.
    Usage: {% url_replace param1='value1' param2='value2' %}
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value is None or value == '':
            if key in query:
                del query[key]
        else:
            query[key] = value
    
@register.simple_tag(takes_context=True)
def toggle_url(context, param, value):
    """
    Toggles a value in a list of GET parameters.
    Used for multi-select filters.
    Usage: {% toggle_url 'ecosystem' 'Chase' %}
    """
    query = context['request'].GET.copy()
    current_values = query.getlist(param)
    
    # Ensure value is treated as string for comparison
    val_str = str(value)
    
    if val_str in current_values:
        current_values.remove(val_str)
    else:
        current_values.append(val_str)
        
    query.setlist(param, current_values)
    return query.urlencode()
