# Generated by Django 5.0.1 on 2025-07-25 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_rename_is_live_to_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='moq',
            field=models.PositiveIntegerField(blank=True, help_text='Retailer MOQ if applicable', null=True),
        ),
    ]
