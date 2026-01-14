from django import template
from django.utils.timesince import timesince
from django.utils import timezone
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def naturaltime_short(value):
    """
    Returns a shortened natural time string, keeping only the most significant unit.
    E.g. "2 days, 4 hours ago" -> "2 days ago".
    "(Verified 2 days ago)" format is handled in template.
    """
    if not value:
        return ""

    if not isinstance(value, (datetime, float, int)):
        # Try to convert if it's not a datetime
         return value

    now = timezone.now()
    
    # If it's a future date or very close
    diff = now - value
    if diff < timedelta(seconds=60):
        return "just now"

    # Get timesince string "2 days, 4 hours"
    ts = timesince(value, now)
    
    # Split by comma and take the first part
    # "2 days, 4 hours" -> "2 days"
    short_ts = ts.split(',')[0]
    
    return f"{short_ts} ago"
