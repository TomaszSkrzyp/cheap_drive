# Generated by Django 5.1.4 on 2025-01-15 18:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0003_auto_20250115_1859'),
        ('refill', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='entry.user'),
        ),
        migrations.AlterField(
            model_name='vehicle_data',
            name='user',
            field=models.ForeignKey(blank=True, help_text='The user who owns the vehicle.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vehicle_data', to='entry.user'),
        ),
    ]
