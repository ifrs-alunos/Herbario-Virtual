# Generated by Django 3.0.2 on 2020-10-05 13:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0025_auto_20200928_1246'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=20, verbose_name='Região')),
            ],
            options={
                'verbose_name': 'Região',
                'verbose_name_plural': 'Regiões',
                'ordering': ['name'],
            },
        ),
        migrations.RemoveField(
            model_name='plant',
            name='occorrence_states',
        ),
        migrations.AddField(
            model_name='state',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='states', to='herbarium.Region'),
        ),
    ]
