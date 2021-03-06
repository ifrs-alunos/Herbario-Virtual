# Generated by Django 3.0.2 on 2020-09-16 16:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0021_division_family'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plant',
            name='division',
        ),
        migrations.AlterField(
            model_name='division',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='family',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='created_at',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Criado em'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='plant',
            name='description',
            field=models.TextField(verbose_name='Descrição'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='family',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plants', to='herbarium.Family'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='scientific_name',
            field=models.CharField(max_length=200, verbose_name='Nome científico'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='slug',
            field=models.SlugField(null=True, verbose_name='Identificador'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='updated_at',
            field=models.DateField(auto_now=True, default=django.utils.timezone.now, verbose_name='Criado em'),
            preserve_default=False,
        ),
    ]
