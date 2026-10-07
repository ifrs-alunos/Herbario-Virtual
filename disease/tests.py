from importlib import import_module

from django.apps import apps as django_apps
from django.test import TestCase

from disease.models import Culture, Disease, PhotoDisease


def criar_doenca(nome='Ferrugem'):
    cultura = Culture.objects.create(name='Soja')

    return Disease.objects.create(
        name_disease=nome,
        scientific_name_disease='Phakopsora pachyrhizi',
        culture_disease=cultura,
        symptoms_disease='sintomas',
        published_disease=True,
    )


def criar_foto(disease, published):
    """Cria uma PhotoDisease sem passar por PhotoDisease.save().

    Ver o comentário equivalente em herbarium/tests.py: o save() exige uma imagem
    Full HD de verdade, e estes testes são sobre o campo `published`.
    """

    foto = PhotoDisease(
        disease=disease, image='doencas/imagens-grandes/x.jpg', published=published
    )
    PhotoDisease.objects.bulk_create([foto])

    return PhotoDisease.objects.get(pk=foto.pk)


class PublishedPhotosTests(TestCase):
    """Disease.published_photos — já existia; aqui fica coberto"""

    def setUp(self):
        self.disease = criar_doenca()

    def test_mostra_apenas_a_foto_aprovada(self):
        aprovada = criar_foto(self.disease, published=True)
        criar_foto(self.disease, published=False)

        self.assertEqual(list(self.disease.published_photos), [aprovada])

    def test_foto_com_published_nulo_nao_aparece(self):
        criar_foto(self.disease, published=None)

        self.assertFalse(self.disease.published_photos.exists())


class HoldExistingPhotosMigrationTests(TestCase):
    """A migração 0003: NULL vira False sem alterar o que o público vê"""

    def setUp(self):
        self.disease = criar_doenca()

        migracao = import_module('disease.migrations.0003_hold_existing_photos')

        self.migrar = lambda: migracao.hold_existing_photos(django_apps, None)

    def test_acervo_antigo_fica_pendente(self):
        antiga = criar_foto(self.disease, published=None)

        self.migrar()

        antiga.refresh_from_db()
        self.assertIs(antiga.published, False)

    def test_nao_altera_o_que_o_publico_ve(self):
        """A regra do deploy: mesmas imagens visíveis antes e depois"""

        aprovada = criar_foto(self.disease, published=True)
        criar_foto(self.disease, published=None)

        antes = list(self.disease.published_photos)
        self.migrar()

        self.assertEqual(antes, [aprovada])
        self.assertEqual(list(self.disease.published_photos), [aprovada])

    def test_e_idempotente(self):
        criar_foto(self.disease, published=None)

        self.migrar()
        self.migrar()

        self.assertEqual(PhotoDisease.objects.filter(published=False).count(), 1)


class CultureSaveTests(TestCase):
    """Culture.save() precisa repassar os argumentos que o ORM lhe entrega"""

    def test_objects_create_funciona(self):
        """Era TypeError: save() estava declarado como `def save(self)`"""

        cultura = Culture.objects.create(name='Trigo')

        self.assertEqual(cultura.slug, 'trigo')

    def test_update_fields_e_respeitado(self):
        cultura = Culture.objects.create(name='Milho')

        cultura.name = 'Milho safrinha'
        cultura.save(update_fields=['name'])
        cultura.refresh_from_db()

        self.assertEqual(cultura.name, 'Milho safrinha')

    def test_slug_existente_nao_e_sobrescrito(self):
        cultura = Culture.objects.create(name='Aveia')

        cultura.name = 'Aveia preta'
        cultura.save()

        self.assertEqual(cultura.slug, 'aveia')
