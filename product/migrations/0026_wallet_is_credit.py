# Generated by Django 4.2.2 on 2023-08-26 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0025_alter_wallet_amount_alter_wallet_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='is_credit',
            field=models.BooleanField(default=True),
        ),
    ]
