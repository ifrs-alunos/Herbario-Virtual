# Generated by Django 3.2.7 on 2024-09-23 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0013_alter_report_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='station',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='alerts.station'),
        ),
    ]
