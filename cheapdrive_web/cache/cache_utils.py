from django.core.exceptions import ObjectDoesNotExist
from .models import Cache

def get_from_cache(key: str):
    """
    Retrieve the cached value if it exists and is not expired.
    """
    try:
        cache_entry = Cache.objects.get(key=key)
        if cache_entry.is_expired():
            cache_entry.delete()  # Optionally, delete expired cache
            return None
        return cache_entry.value
    except ObjectDoesNotExist:
        return None

def set_cache(key: str, value: dict, timeout: int = 3600):
    """
    Set a value in the cache. If the key exists, it will be updated.
    """
    cache_entry, created = Cache.objects.update_or_create(
        key=key,
        defaults={'value': value, 'timeout': timeout},
    )
    return cache_entry
