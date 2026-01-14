from functools import wraps
from django.utils.cache import patch_cache_control

def cache_control_header(max_age=300, s_maxage=None, public=False, private=False):
    """
    Decorator to set the Cache-Control header for a view.
    
    Usage:
        @cache_control_header(max_age=600, public=True)
        def my_view(request):
            ...
            
    :param max_age: Time in seconds for browser caching.
    :param s_maxage: Time in seconds for shared cache (CDN/Firebase).
    :param public: If True, marks as public (cachable by CDNs even if authed - USE CAUTION).
    :param private: If True, marks as private (only browser cache).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            # Build cache control arguments
            kwargs_dict = {'max_age': max_age}
            if s_maxage is not None:
                kwargs_dict['s_maxage'] = s_maxage
            if public:
                kwargs_dict['public'] = True
            if private:
                kwargs_dict['private'] = True
                
            patch_cache_control(response, **kwargs_dict)
            return response
        return _wrapped_view
    return decorator
