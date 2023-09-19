# Generated by Django 4.2.2 on 2023-08-20 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_order_orderitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='billing_address1',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='billing_address2',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='billing_city',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='billing_country',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='billing_email',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='billing_state',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default='None'),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_quantity',
            field=models.IntegerField(default='None'),
        ),
    ]
