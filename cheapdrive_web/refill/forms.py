from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

class LoadDataForm(forms.Form):
    """
    Form for loading trip and vehicle data including addresses, fuel details, and driving conditions.
    """
    origin_address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"id": "id_origin_address", "class": "autocomplete"})
    )
    destination_address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"id": "id_destination_address", "class": "autocomplete"})
    )
    tank_size = forms.FloatField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={"id": "id_tank_size", "step": "0.1"}),
        label="Tank Size (Liters)"
    )
    price_of_fuel = forms.FloatField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={"id": "id_price_of_fuel", "step": "0.01"}),
        label="Price of Fuel per Liter"
    )
    currency = forms.ChoiceField(
        choices=[("PLN", "PLN"), ("USD", "USD"), ("EUR", "EUR"), ("GBP", "GBP")],
        required=True
    )
    fuel_consumption_per_100km = forms.FloatField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={"id": "id_fuel_consumption_per_100km", "step": "0.1"}),
        label="Average Fuel Consumption (L/100km)"
    )
    fuel_type = forms.ChoiceField(
        choices=[("PB95", "PB95"), ("Diesel", "Diesel"), ("PB98", "PB98"), ("LPG", "LPG")],
        required=True,
        widget=forms.Select(attrs={"id": "id_fuel_type"}),
        label="Fuel Type"
    )
    cur_fuel_liters_check = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"id": "id_cur_fuel_liters_check"}),
        label="Enter current fuel in liters",
        initial=True
    )
    cur_fuel_percentage_check = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"id": "id_cur_fuel_percentage_check"}),
        label="Enter current fuel in percentage",
        initial=False
    )
    cur_fuel = forms.FloatField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"id": "id_cur_fuel"}),
        label="Current Fuel"
    )
    cur_fuel_percentage = forms.FloatField(
        min_value=0,
        max_value=100,
        required=False,
        widget=forms.NumberInput(attrs={"id": "id_cur_fuel_percentage"}),
        label="Current Fuel Percentage"
    )
    DRIVING_CONDITIONS = [
        ("city", "City Driving (Avg: 40 km/h)"),
        ("mixed", "Mixed Driving (Avg: 60 km/h)"),
        ("highway", "Highway Driving (Avg: 90 km/h)")
    ]
    driving_conditions = forms.ChoiceField(
        choices=DRIVING_CONDITIONS,
        required=True,
        widget=forms.RadioSelect(),
        label="Select Your Typical Driving Conditions"
    )

    def clean(self):
        cleaned_data = super().clean()
    
        cur_fuel_liters_check = cleaned_data.get("cur_fuel_liters_check", False)
        cur_fuel_percentage_check = cleaned_data.get("cur_fuel_percentage_check", False)
        tank_size = cleaned_data.get("tank_size", 0)
        cur_fuel = cleaned_data.get("cur_fuel")
        cur_fuel_percentage = cleaned_data.get("cur_fuel_percentage")
    
        # Ensure exactly one method of specifying current fuel is selected.
        if not cur_fuel_liters_check and not cur_fuel_percentage_check:
            raise ValidationError("You must select either liters or percentage for current fuel.")
        if cur_fuel_liters_check and cur_fuel_percentage_check:
            raise ValidationError("You cannot select both liters and percentage for current fuel.")
    
        if tank_size <= 0:
            raise ValidationError({"tank_size": "Tank size must be a positive value."})
    
        # Validate current fuel in liters.
        if cur_fuel_liters_check:
            if cur_fuel is None:
                raise ValidationError({"cur_fuel": "Please enter a valid value for current fuel in liters."})
            if cur_fuel < 0:
                raise ValidationError({"cur_fuel": "Current fuel must be a non-negative value."})
            if cur_fuel > tank_size:
                raise ValidationError({"cur_fuel": "Current fuel cannot exceed the tank size."})
    
        # Validate and convert current fuel percentage to liters.
        elif cur_fuel_percentage_check:
            if cur_fuel_percentage is None:
                raise ValidationError({"cur_fuel_percentage": "Please enter a valid value for current fuel percentage."})
            if cur_fuel_percentage < 0 or cur_fuel_percentage > 100:
                raise ValidationError({"cur_fuel_percentage": "Current fuel percentage must be between 0 and 100."})
            cleaned_data["cur_fuel"] = (cur_fuel_percentage / 100) * tank_size
    
        # Helper function to remove trailing zeros from numeric values.
        def remove_trailing_zeros(value):
            return str(Decimal(value).normalize()) if value is not None else value
    
        cleaned_data["tank_size"] = remove_trailing_zeros(cleaned_data.get("tank_size"))
        cleaned_data["price_of_fuel"] = remove_trailing_zeros(cleaned_data.get("price_of_fuel"))
        cleaned_data["fuel_consumption_per_100km"] = remove_trailing_zeros(cleaned_data.get("fuel_consumption_per_100km"))
        cleaned_data["cur_fuel"] = remove_trailing_zeros(cleaned_data.get("cur_fuel"))
    
        return cleaned_data
