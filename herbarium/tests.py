from importlib import import_module

from django.apps import apps as django_apps
from django.test import TestCase

from herbarium.models import Family, Photo, Plant


def criar_planta(nome='Buva'):
    """Planta mínima para pendurar fotos"""

    familia = Family.objects.create(name='Asteraceae')

    return Plant.objects.create(
        name=nome,
        scientific_name='Conyza bonariensis',
        family=familia,
        description='descrição',
        importance='importância',
        published=True,
    )


def criar_foto(plant, published):
    """Cria uma Photo sem passar por Photo.save().

    `Photo.save()` abre a imagem com o Pillow e exige no mínimo 1920x1080. Estes
    testes são sobre o campo `published`, não sobre o processamento da imagem, e
    o bulk_create escapa do save() sem precisar de um arquivo Full HD de verdade.
    """

    foto = Photo(plant=plant, image='plantas/imagens-grandes/x.jpg', published=published)
    Photo.objects.bulk_create([foto])

    return Photo.objects.get(pk=foto.pk)


class PublishedPhotosTests(TestCase):
    """Plant.published_photos — o filtro que faz a aprovação valer no site público"""

    def setUp(self):
        self.plant = criar_planta()

    def test_mostra_apenas_a_foto_aprovada(self):
        aprovada = criar_foto(self.plant, published=True)
        criar_foto(self.plant, published=False)

        self.assertEqual(list(self.plant.published_photos), [aprovada])

    def test_foto_pendente_nao_aparece(self):
        criar_foto(self.plant, published=False)

        self.assertFalse(self.plant.published_photos.exists())

    def test_foto_com_published_nulo_nao_aparece(self):
        """NULL é o estado do acervo antigo; a data migration 0004 o resolve"""

        criar_foto(self.plant, published=None)

        self.assertFalse(self.plant.published_photos.exists())

    def test_planta_sem_foto_nao_quebra(self):
        self.assertFalse(self.plant.published_photos.exists())


class PublishExistingPhotosMigrationTests(TestCase):
    """A migração 0004, que impede o deploy de apagar imagens do site público"""

    def setUp(self):
        self.plant = criar_planta()

        # O módulo começa com dígito, então não dá para importar pela sintaxe normal.
        # Chamamos a função com o registro real de apps: ela só faz um update()
        # sobre um campo que não mudou de forma desde a migração.
        migracao = import_module('herbarium.migrations.0004_publish_existing_photos')

        self.migrar = lambda: migracao.publish_existing_photos(django_apps, None)

    def test_publica_o_acervo_antigo(self):
        antiga = criar_foto(self.plant, published=None)

        self.migrar()

        antiga.refresh_from_db()
        self.assertTrue(antiga.published)

    def test_nao_mexe_no_que_ja_tem_valor(self):
        recusada = criar_foto(self.plant, published=False)
        aprovada = criar_foto(self.plant, published=True)

        self.migrar()

        recusada.refresh_from_db()
        aprovada.refresh_from_db()
        self.assertFalse(recusada.published)
        self.assertTrue(aprovada.published)

    def test_e_idempotente(self):
        criar_foto(self.plant, published=None)

        self.migrar()
        self.migrar()

        self.assertEqual(Photo.objects.filter(published=True).count(), 1)
