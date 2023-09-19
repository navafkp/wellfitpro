# Generated by Django 4.2.2 on 2023-08-20 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0015_alter_order_total_quantity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='total_quantity',
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_charge',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]