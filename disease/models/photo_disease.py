from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify

from core.utils import make_small_image
from core.validators import MIN_HEIGHT, MIN_WIDTH, validate_min_resolution
from disease.models.disease import Disease


def disease_directory_path(instance, filename):
    """Esta função retorna o diretório onde as imagens grandes de uma planta devem ser armazenadas"""

    disease_name = slugify({instance.disease.name_disease})

    return 'doencas/imagens-grandes/{}/{}'.format(disease_name, filename)


def small_disease_directory_path(instance, filename):
    """Esta função retorna o diretório onde as imagens pequenas de uma planta devem ser armazenadas"""

    disease_name = slugify({instance.disease.name_disease})

    # Arruma um pequeno bug de redundancia de path
    filename = filename.split('/')[-1]

    return 'doencas/imagens-pequenas/{}/{}'.format(disease_name, filename)

class PhotoDisease(models.Model):
    """Esta classe define os atributos que compõem uma foto de uma doença, permitindo que ela tenha múltiplas imagens"""

    # Relaciona as fotos com a planta
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='photos', verbose_name="Doença")

    # Campo que contém uma imagem e indica a função que retorna onde a imagem deve ser guardada
    image = models.ImageField(
        upload_to=disease_directory_path,
        verbose_name="Imagens",
        max_length=500,
        validators=[validate_min_resolution],
        help_text="Resolução mínima: {}x{} (Full HD).".format(MIN_WIDTH, MIN_HEIGHT),
    )

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

        # Ver o comentário equivalente em herbarium/models/photo.py.
        if pillow_img_width >= MIN_WIDTH and pillow_img_height >= MIN_HEIGHT:
            # Cria a imagem pequena e insere no campo do modelo
            self.small_image = make_small_image(self.image)
            super().save(*args, **kwargs)
        else:
            raise ValueError(
                "Imagem da doença {} não contém a dimensão mínima indicada (Full HD: 1920x1080)".format(self.image))

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'
        # Ver o comentário equivalente em herbarium/models/photo.py: aprovar foto
        # deixa de depender de change_disease.
        permissions = [('approve_photodisease', 'Pode aprovar fotos de doenças')]
