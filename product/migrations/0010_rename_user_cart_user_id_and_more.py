# Generated by Django 4.2.4 on 2023-08-17 17:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0009_cart_created_at_alter_cart_discount_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cart',
            old_name='user',
            new_name='user_id',
        ),
        migrations.RenameField(
            model_name='cartitem',
            old_name='product',
            new_name='product_id',
        ),
        migrations.AddField(
            model_name='cartitem',
            name='cart_id',
            field=models.ForeignKey(default=9999, on_delete=django.db.models.deletion.CASCADE, to='product.cart'),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='image',
            field=models.ImageField(upload_to='carted_image'),
        ),
    ]
