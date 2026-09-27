from django.db import migrations


def publish_existing_photos(apps, schema_editor):
    """Marca como publicadas as fotos de planta que já estavam no ar.

    Até esta versão, `herbarium/templates/herbarium/*.html` exibia `plant.photos`
    sem filtro nenhum: **toda** foto de planta aparecia no site, aprovada ou não.
    Os templates passam agora a usar `Plant.published_photos`, que exige
    `published=True` — e o acervo antigo está com `published=NULL`, porque a view
    de solicitação nunca chegou a gravar o `False` que pretendia.

    Sem esta migração, o deploy apagaria do site público todas as imagens do
    herbário de plantas. O critério é preservação de estado, não "publicar tudo":
    aqui vira True justamente porque hoje todas estão visíveis.

    Consequência aceita: as fotos que estavam na fila de revisão saem daqui já
    publicadas. Elas já estavam no ar antes desta migração. A fila passa a valer
    para o que for enviado a partir do deploy.

    Compare com disease/migrations/0003_hold_existing_photos.py, que faz o
    oposto pelo mesmo motivo.
    """

    Photo = apps.get_model('herbarium', 'Photo')

    Photo.objects.filter(published__isnull=True).update(published=True)


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0003_alter_photo_options'),
    ]

    operations = [
        # Sem reverso: voltar exigiria saber quais linhas eram NULL antes, e essa
        # informação se perde no update.
        migrations.RunPython(publish_existing_photos, migrations.RunPython.noop),
    ]
