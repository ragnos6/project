# Generated by Django 5.1.2 on 2024-10-24 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vehicle',
            options={'ordering': ['-year_of_production'], 'verbose_name': 'Автомобиль', 'verbose_name_plural': 'Автомобили'},
        ),
    ]
