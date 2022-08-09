from django.db import models
from PIL import Image
from core.utils import make_small_image
from django.utils.text import slugify
from .plant import Plant


def plant_directory_path(instance, filename):
    """Esta função retorna o diretório onde as imagens grandes de uma planta devem ser armazenadas"""

    plant_name = slugify(instance.plant.name)

    return 'plantas/imagens-grandes/{}/{}'.format(plant_name, filename)


def small_plant_directory_path(instance, filename):
    """Esta função retorna o diretório onde as imagens pequenas de uma planta devem ser armazenadas"""

    plant_name = slugify({instance.plant.name})

    # Arruma um pequeno bug de redundancia de path
    filename = filename.split('/')[-1]

    return 'plantas/imagens-pequenas/{}/{}'.format(plant_name, filename)


class Photo(models.Model):
    """Esta classe define os atributos que compõem uma foto de uma planta, permitindo que ela tenha múltiplas imagens"""

    # Relaciona as fotos com a planta
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='photos', verbose_name="Planta")

    # Campo que contém uma imagem e indica a função que retorna onde a imagem deve ser guardada
    image = models.ImageField(upload_to=plant_directory_path, verbose_name="Imagens")

    # Cria um campo não editável que conterá imagens pequenas geradas a partir das imagens maiores
    small_image = models.ImageField(upload_to=small_plant_directory_path, editable=False, null=True)

    published = models.BooleanField(verbose_name="Publicado", null=True)

    def __str__(self):
        return self.image.name

    @property
    def get_contributor(self):

        query = self.photosolicitation_set.all()
        contributor_name = self.photosolicitation_set.all()[0].user.profile.name if query else False
        contributor = str(f'Fonte: {contributor_name}' if contributor_name else '')

        return contributor

    # Sobreescreve o método save da classe
    def save(self, *args, **kwargs):
        # Realiza o processamento na imagem cadastrada (self.image) e guarda o retorno no atributo small_image
        pillow_img = Image.open(self.image)

        pillow_img_width, pillow_img_height = pillow_img.size

        # Especificando tamanho mínimo como Full HD
        if (pillow_img_width >= 1920 and pillow_img_height >= 1080):
            # Cria a imagem pequena e insere no campo do modelo
            self.small_image = make_small_image(self.image)
            super().save(*args, **kwargs)
        else:
            raise ValueError(
                "Imagem da planta {} não contém a dimensão mínima indicada (Full HD: 1920x1080)".format(self.image))

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'
