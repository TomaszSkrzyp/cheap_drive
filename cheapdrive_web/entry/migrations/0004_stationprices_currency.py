# Generated by Django 5.1.4 on 2025-01-27 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0003_auto_20250115_1859'),
    ]

    operations = [
        migrations.AddField(
            model_name='stationprices',
            name='currency',
            field=models.CharField(default='PLN', help_text='The currency of the purchase price.', max_length=3),
        ),
    ]
