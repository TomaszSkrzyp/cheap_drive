
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import AbstractUser,UserManager
from django.db.models.fields import related

class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    
    This model enforces unique email addresses, and customizes the groups and permissions
    through unique related names for better flexibility in querying and managing users.
    It uses Django's built-in UserManager for handling user-related queries and operations.
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
    
    This model holds pricing information for different fuel types (e.g., Diesel, LPG, PB95, PB98) 
    at various fuel stations. Each price field is represented as a decimal value and stored with 
    the associated currency (defaulted to PLN). The model is linked to specific brands through 
    the `BrandChoices` enumeration.
    """

    class BrandChoices(models.TextChoices):
        """
        Enumeration for different fuel station brands.
    
        This enumeration lists various fuel station brands, including popular ones like 'Amic', 'BP', 
        'Moya', 'Total', and others. The enumeration is used in the `brand_name` field of the `StationPrices` model.
        """

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
    
    This model includes an address, geographic location (using GIS for geographic data), and a 
    foreign key to the `StationPrices` model, which holds the fuel price details. The `location` 
    field uses Django's GIS `PointField` to store the geographical coordinates of the station.
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