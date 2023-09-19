# Generated by Django 4.2.4 on 2023-08-27 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0028_alter_wallet_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.IntegerField(choices=[(1, 'Order Initiated'), (2, 'Order Processing'), (3, 'Shipped'), (4, 'Delivered')], default=1),
        ),
    ]