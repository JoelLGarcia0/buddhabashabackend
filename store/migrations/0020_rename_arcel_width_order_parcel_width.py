# Generated by Django 5.2.3 on 2025-07-23 21:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0019_order_arcel_width_order_parcel_height_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='arcel_width',
            new_name='parcel_width',
        ),
    ]
