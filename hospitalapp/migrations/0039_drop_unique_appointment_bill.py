# Generated manually to drop unique_appointment_bill constraint
from django.db import migrations

def drop_unique_appointment_bill(apps, schema_editor):
    if schema_editor.connection.vendor == 'mysql':
        with schema_editor.connection.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE bills DROP INDEX unique_appointment_bill")
            except Exception as e:
                # Ignore if already dropped or not exists
                print(f"Skipping dropping unique_appointment_bill constraint: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('hospitalapp', '0038_biomedicalasset_inventoryitem_supplier_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_unique_appointment_bill, reverse_code=migrations.RunPython.noop),
    ]
