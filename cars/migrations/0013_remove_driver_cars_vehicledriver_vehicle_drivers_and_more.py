# Generated by Django 5.1.2 on 2024-10-29 08:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0012_alter_driver_enterprise_alter_vehicle_enterprise'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='driver',
            name='cars',
        ),
        migrations.CreateModel(
            name='VehicleDriver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cars.driver')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cars.vehicle')),
            ],
        ),
        migrations.AddField(
            model_name='vehicle',
            name='drivers',
            field=models.ManyToManyField(related_name='drivers', through='cars.VehicleDriver', to='cars.driver'),
        ),
        migrations.DeleteModel(
            name='CarDriver',
        ),
    ]