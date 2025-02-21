from django.core.exceptions import ObjectDoesNotExist
from .models import Cache

def get_from_cache(key: str):
    """
    Retrieve the cached value if it exists and is not expired.

    Args:
        key (str): The key for the cache entry to be retrieved.

    Returns:
        The cached value if the key exists and is not expired; otherwise, returns None.

    Raises:
        ObjectDoesNotExist: If the cache entry with the given key does not exist.
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

    Args:
        key (str): The key under which the value will be stored in the cache.
        value (dict): The value to be stored in the cache.
        timeout (int, optional): The timeout for cache expiry in seconds. Defaults to 3600 seconds (1 hour).

    Returns:
        The Cache object representing the created or updated cache entry.
    """

    cache_entry, created = Cache.objects.update_or_create(
        key=key,
        defaults={'value': value, 'timeout': timeout},
    )
    return cache_entry
