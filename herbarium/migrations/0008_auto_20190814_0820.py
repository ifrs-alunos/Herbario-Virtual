# Generated by Django 2.2.2 on 2019-08-14 11:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0007_plant_images'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='division',
            field=models.CharField(blank=True, choices=[('dicotiledoneas', 'Monocotiledôneas'), ('monocotiledoneas', 'Monocotiledôneas')], max_length=100, verbose_name='Divisão'),
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to='images')),
                ('plant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='herbarium.Plant')),
            ],
        ),
    ]
