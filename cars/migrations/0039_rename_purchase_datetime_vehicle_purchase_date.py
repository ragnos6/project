# Generated by Django 5.1.2 on 2024-12-04 17:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0038_rename_purchase_date_vehicle_purchase_datetime'),
    ]

    operations = [
        migrations.RenameField(
            model_name='vehicle',
            old_name='purchase_datetime',
            new_name='purchase_date',
        ),
    ]