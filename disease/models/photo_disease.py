from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify

from disease.models.disease import Disease


def disease_directory_path(instance, filename):
    '''Esta função retorna o diretório onde as imagens grandes de uma planta devem ser armazenadas'''

    disease_name = slugify({instance.disease.name_disease})

    return 'doencas/imagens-grandes/{}/{}'.format(disease_name, filename)


def small_disease_directory_path(instance, filename):
    '''Esta função retorna o diretório onde as imagens pequenas de uma planta devem ser armazenadas'''

    disease_name = slugify({instance.disease.name_disease})

    # Arruma um pequeno bug de redundancia de path
    filename = filename.split('/')[-1]

    return 'doencas/imagens-pequenas/{}/{}'.format(disease_name, filename)


def make_small_image(image, size=(854, 480)):
    '''Esta função retorna uma imagem miniatura com um tamanho específico a partir de uma imagem maior'''

    im = Image.open(image)  # Abre a imagem com o Pillow

    im.convert('RGB')

    im.thumbnail(size)  # Redimensiona a imagem com o tamanho padrão descrito nos parâmetros

    thumb_io = BytesIO()  # Cria um objeto BytesIO

    im.save(thumb_io, 'JPEG', quality=100)  # Salva imagem para um objeto BytesIO

    thumbnail = File(thumb_io, name=image.name)  # Cria um objeto File 'amigável' ao Django

    return thumbnail


class PhotoDisease(models.Model):
    '''Esta classe define os atributos que compõem uma foto de uma doença, permitindo que ela tenha múltiplas imagens'''

    # Relaciona as fotos com a planta
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='photos', verbose_name="Doença")

    # Campo que contém uma imagem e indica a função que retorna onde a imagem deve ser guardada
    image = models.ImageField(upload_to=disease_directory_path, verbose_name="Imagens",max_length=500)

    # Cria um campo não editável que conterá imagens pequenas geradas a partir das imagens maiores
    small_image = models.ImageField(upload_to=small_disease_directory_path, editable=False, null=True, max_length=500)

    # source_disease_photo = models.CharField('Referência da foto', blank=True, help_text='Insira a referência
    # utilizada', default='Desconhecido', max_length=100)

    published = models.BooleanField(verbose_name="Publicado", null=True)

    def __str__(self):
        return self.image.name

    @property
    def get_contributor(self):

        query = self.diseasephotosolicitation_set.all()
        try:
            contributor_name = self.diseasephotosolicitation_set.all()[0].user.profile.name if query else False
        except:
            contributor_name = False
        contributor = str(f'Fonte: {contributor_name}' if contributor_name else '')

        return contributor

    # Sobreescreve o método save da classe
    def save(self, *args, **kwargs):
        # Realiza o processamento na imagem cadastrada (self.image) e guarda o retorno no atributo small_image
        pillow_img = Image.open(self.image)

        pillow_img_width, pillow_img_height = pillow_img.size

        # Especificando tamanho mínimo como Full HD
        if pillow_img_width >= 1920 and pillow_img_height >= 1080:
            # Cria a imagem pequena e insere no campo do modelo
            self.small_image = make_small_image(self.image)
            super().save(*args, **kwargs)
        else:
            raise ValueError(
                "Imagem da doença {} não contém a dimensão mínima indicada (Full HD: 1920x1080)".format(self.image))

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

