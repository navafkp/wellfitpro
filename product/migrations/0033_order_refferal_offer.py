# Generated by Django 4.2.4 on 2023-09-11 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0032_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='refferal_offer',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
