# Generated by Django 4.2.2 on 2023-08-21 03:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_country_state_shippingaddress_address'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ShippingAddress',
        ),
    ]
