# Generated by Django 2.2.2 on 2019-08-13 12:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0005_auto_20190702_1115'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plant',
            name='order',
        ),
        migrations.RemoveField(
            model_name='plant',
            name='plant_class',
        ),
    ]
