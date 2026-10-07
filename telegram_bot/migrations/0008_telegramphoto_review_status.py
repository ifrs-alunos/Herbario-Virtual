from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def preencher_status(apps, schema_editor):
    """Dá status às imagens de treino que já existiam.

    Com data de aprovação: aprovada. Sem: aguardando revisão. As reprovadas
    antes desta migração foram apagadas, então não há o que recuperar.
    """

    TelegramPhoto = apps.get_model('telegram_bot', 'TelegramPhoto')
    treino = TelegramPhoto.objects.filter(purpose='training')

    treino.filter(reviewed_at__isnull=False).update(review_status='approved')
    treino.filter(reviewed_at__isnull=True).update(review_status='pending')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('telegram_bot', '0007_telegramphoto_descricao_e_categoria'),
    ]

    operations = [
        # Renomeados porque passam a registrar também a reprovação
        migrations.RenameField(
            model_name='telegramphoto',
            old_name='approved_at',
            new_name='reviewed_at',
        ),
        migrations.RenameField(
            model_name='telegramphoto',
            old_name='approved_by',
            new_name='reviewed_by',
        ),
        migrations.AlterField(
            model_name='telegramphoto',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Revisada em'),
        ),
        migrations.AlterField(
            model_name='telegramphoto',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_telegram_photos', to=settings.AUTH_USER_MODEL, verbose_name='Revisada por'),
        ),
        migrations.AddField(
            model_name='telegramphoto',
            name='review_status',
            field=models.CharField(blank=True, choices=[('pending', 'Aguardando revisão'), ('approved', 'Aprovada'), ('rejected', 'Reprovada')], db_index=True, max_length=20, verbose_name='Revisão'),
        ),
        migrations.RunPython(preencher_status, migrations.RunPython.noop),
    ]
