# Generated by Django 2.2.2 on 2019-08-14 11:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0008_auto_20190814_0820'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='photo',
            options={'verbose_name': 'Foto', 'verbose_name_plural': 'Fotos'},
        ),
        migrations.RenameField(
            model_name='photo',
            old_name='photo',
            new_name='image',
        ),
    ]
