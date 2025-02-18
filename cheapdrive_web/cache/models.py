from django.db import models

from django.utils import timezone
# Create your models here.

class Cache(models.Model):
    """
    Custom cache model that will store cache data.
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
