# Generated by Django 5.1.4 on 2025-01-30 15:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0004_stationprices_currency'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stationprices',
            name='currency',
        ),
    ]
