# Generated by Django 4.2.4 on 2023-08-17 17:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_rename_user_cart_user_id_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cart',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='cartitem',
            old_name='cart_id',
            new_name='cart',
        ),
        migrations.RenameField(
            model_name='cartitem',
            old_name='product_id',
            new_name='product',
        ),
    ]
