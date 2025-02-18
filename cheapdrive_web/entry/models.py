
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import AbstractUser,UserManager
from django.db.models.fields import related

class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    Enforces unique email addresses and uses custom group/permission related names.
    """
    email = models.EmailField(unique=True)
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups"  # Unique related_name.
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions"  # Unique related_name.
    )
    objects = UserManager()


class StationPrices(models.Model):
    """
    Model representing fuel station prices for different fuel types.
    """
    class BrandChoices(models.TextChoices):
        AMIC = "amic", "Amic"
        LOTOS = "lotos", "Lotos"
        LOTOS_OPTIMA = "lotos optima", "Lotos Optima"
        CIRCLE_K = "circle-k", "Circle-k"
        BP = "bp", "BP"
        MOYA = "moya", "Moya"
        AUCHAN = "auchan", "Auchan"
        TESCO = "tesco", "Tesco"
        CARREFOUR = "carrefour", "Carrefour"
        OLKOP = "olkop", "Olkop"
        LECLERC = "leclerc", "Leclerc"
        INTERMARCHE = "intermarche", "Intermarche"
        MOL = "mol", "MOL"
        HUZAR = "huzar", "Huzar"
        TOTAL = "total", "Total"
        POLSKA = "polska", "Polska"

    brand_name = models.CharField(
        max_length=20,
        choices=BrandChoices.choices,
        help_text="Select the fuel station brand."
    )
    currency = models.CharField(
        max_length=3,
        default="PLN",
        help_text="The currency of the purchase price."
    )
    diesel_price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Price per liter of Diesel in PLN",
        null=True
    )
    lpg_price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Price per liter of LPG in PLN",
        null=True
    )
    pb95_price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Price per liter of BP95 in PLN",
        null=True
    )
    pb98_price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Price per liter of BP98 in PLN",
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)


class Station(models.Model):
    """
    Model representing a fuel station, including its geographic location and associated station prices.
    """
    address = models.CharField(max_length=100, null=True)
    location = gis_models.PointField(geography=True)
    station_prices = models.ForeignKey(
        StationPrices,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stations"
    )