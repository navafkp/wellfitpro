# Generated by Django 4.2.4 on 2023-08-10 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_alter_fitproduct_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='fitproduct',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]