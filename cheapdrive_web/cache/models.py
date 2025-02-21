from django.db import models

from django.utils import timezone
# Create your models here.

class Cache(models.Model):
    """
    Custom cache model that will store cache data.

    Attributes:
        key (str): A unique key used to identify the cache entry.
        value (dict): The cached data stored in JSON format.
        created_at (datetime): The timestamp when the cache entry was created.
        updated_at (datetime): The timestamp when the cache entry was last updated.
        timeout (int): The expiration time (in seconds) for the cache entry.

    Methods:
        is_expired: Checks if the cache has expired based on the timeout.
        __str__: Returns a string representation of the Cache object, displaying the cache key.
    """
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField()  # or TextField depending on your data format
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    timeout = models.PositiveIntegerField(default=3600)  # Cache expiry time in seconds

    def is_expired(self):
        """Check if the cache has expired based on the timeout."""
        return timezone.now() > self.updated_at + timezone.timedelta(seconds=self.timeout)

    def __str__(self):
        return f"Cache key: {self.key}"

    class Meta:
        db_table = 'cache'
