# Generated by Django 3.2.7 on 2024-08-19 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0007_requirement_min_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='IntermediaryRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Requisito intermediário',
                'verbose_name_plural': 'Requisitos intermediários',
            },
        ),
        migrations.DeleteModel(
            name='Formula',
        ),
        migrations.AlterField(
            model_name='requirement',
            name='min_time',
            field=models.FloatField(blank=True, null=True, verbose_name='Tempo mínimo'),
        ),
        migrations.AddField(
            model_name='intermediaryrequirement',
            name='requirements',
            field=models.ManyToManyField(to='alerts.Requirement', verbose_name='Requisitos'),
        ),
    ]