# Generated by Django 5.0.1 on 2025-07-10 00:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0006_remove_dailymetrics_app_dailyme_is_stoc_2989f2_idx_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dailymetrics",
            name="lost_sales",
        ),
    ]
