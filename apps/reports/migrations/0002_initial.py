from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('reports', '0001_initial'),
    ]

    # This migration exists to preserve the migration history shape, but the
    # schema is already created in 0001_initial.
    operations = []
