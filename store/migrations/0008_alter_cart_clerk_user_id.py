# Generated by Django 5.2.3 on 2025-06-30 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_alter_product_stock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='clerk_user_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
