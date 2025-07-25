from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("app", "0002_alter_product_options_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE app_product RENAME COLUMN is_live TO is_active;",
            reverse_sql="ALTER TABLE app_product RENAME COLUMN is_active TO is_live;",
        ),
    ]
