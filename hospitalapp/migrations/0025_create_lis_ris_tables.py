# Migration 0025: Create new LIS/RIS tables that don't yet exist in the DB.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospitalapp', '0024_laborder_created_by_laborder_modified_by_and_more'),
    ]

    operations = [
    ]
