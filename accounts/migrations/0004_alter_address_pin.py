# Generated by Django 4.2.2 on 2023-08-21 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_delete_shippingaddress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='pin',
            field=models.CharField(max_length=20),
        ),
    ]