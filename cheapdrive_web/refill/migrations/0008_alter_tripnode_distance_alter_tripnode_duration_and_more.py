# Generated by Django 5.1.4 on 2025-01-30 15:12

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('refill', '0007_alter_tripnode_fuel_refilled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tripnode',
            name='distance',
            field=models.DecimalField(decimal_places=1, help_text='Distance of trip', max_digits=5, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='tripnode',
            name='duration',
            field=models.DecimalField(decimal_places=1, help_text='Duration of the trip - in minutes', max_digits=5, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='tripnode',
            name='fuel_refilled',
            field=models.DecimalField(blank=True, decimal_places=1, help_text='Fuel added at the beggining of the node', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='vehicle_data',
            name='need_refill',
            field=models.BooleanField(blank=True, help_text='Information wheter the vehicle needs refill.', null=True),
        ),
    ]
