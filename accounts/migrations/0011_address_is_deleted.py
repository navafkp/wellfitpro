# Generated by Django 4.2.2 on 2023-09-14 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_notifications_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
