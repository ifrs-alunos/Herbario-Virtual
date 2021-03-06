# Generated by Django 2.2.2 on 2019-08-14 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0013_auto_20190814_0919'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plant',
            name='images',
        ),
        migrations.AlterField(
            model_name='photo',
            name='image',
            field=models.ImageField(upload_to='images'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='division',
            field=models.CharField(blank=True, choices=[('dicotiledoneas', 'Dicotiledôneas'), ('monocotiledoneas', 'Monocotiledôneas')], max_length=100, verbose_name='Divisão'),
        ),
    ]
