# Generated by Django 4.2.2 on 2023-08-17 12:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_fitproduct_short_description_alter_fitproduct_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('name', models.CharField(max_length=80)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('slug', models.CharField(max_length=100)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productimage')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.fitproduct')),
            ],
        ),
    ]
