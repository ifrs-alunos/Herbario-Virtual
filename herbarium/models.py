from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify

class Region(models.Model):
    '''Esta classe define uma região de um país'''

    name = models.CharField('Região', blank=True, max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'
        ordering = ['name']

class State(models.Model):
    '''Esta classe define um estado (unidade federativa) que pertence à uma região'''

    name = models.CharField('Nome', blank=False, max_length=20)
    initials = models.CharField('Sigla', blank=False, max_length=2, null=True)

    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="states", null=True, verbose_name="Região")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['name']

class Family(models.Model):
    '''Esta classe define uma família de uma planta'''

    # Cria uma variável do tipo texto com máximo de 100 caracteres
    name = models.CharField('Nome', blank=False, max_length=100)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.name

    def get_slug(self):
        return slugify(self.name)

    class Meta:
        verbose_name = 'Família'
        verbose_name_plural = 'Famílias'
        ordering = ['name']

class Plant(models.Model):
    '''Esta classe define uma planta cujas informações serão utilizadas em um herbário virtual'''

    name = models.CharField('Nome', blank=False, max_length=100)
    scientific_name = models.CharField('Nome científico', blank=False, max_length=200)
    complementary_scientific_name = models.CharField(verbose_name="Nome Científico Complementar", max_length=60, blank=True, null=True)

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="plants", verbose_name="Família")

    # Torna um conjunto de palavras passíveis para serem usadas como um URL
    slug = models.SlugField('Identificador', blank=True, null=True, unique=True)

    description = models.TextField('Descrição', blank=False)

    importance = models.TextField('Importância', blank=False, null=True)

    occurrence_regions = models.ManyToManyField(Region, verbose_name="Regiões de Ocorrência")

    created_at = models.DateField('Criado em', auto_now_add=True, null=False)
    updated_at = models.DateField('Criado em', auto_now=True, null=False)

    published = models.BooleanField(verbose_name="Publicado", null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.name)
        
        super().save(*args, **kwargs)



    class Meta:
        verbose_name = 'Planta'
        verbose_name_plural = 'Plantas'
        ordering = ['name']
        permissions = [('contribute_with_plants', 'Pode contribuir com plantas')]

def plant_directory_path(instance, filename):
    '''Esta função retorna o diretório onde as imagens grandes de uma planta devem ser armazenadas'''

    plant_name = slugify(instance.plant.name)

    return 'plantas/imagens-grandes/{}/{}'.format(plant_name, filename)

def small_plant_directory_path(instance, filename):
    '''Esta função retorna o diretório onde as imagens pequenas de uma planta devem ser armazenadas'''

    plant_name = slugify(instance.plant.name)

    return 'plantas/imagens-pequenas/{}/{}'.format(plant_name, filename)

def make_small_image(image, size=(854, 480)):
    '''Esta função retorna uma imagem miniatura com um tamanho específico a partir de uma imagem maior'''

    im = Image.open(image) # Abre a imagem com o Pillow

    im.convert('RGB')

    im.thumbnail(size) # Redimensiona a imagem com o tamanho padrão descrito nos parâmetros

    thumb_io = BytesIO() # Cria um objeto BytesIO

    im.save(thumb_io, 'JPEG', quality=100) # Salva imagem para um objeto BytesIO 

    thumbnail = File(thumb_io, name=image.name) # Cria um objeto File 'amigável' ao Django 

    return thumbnail

class Photo(models.Model):
    '''Esta classe define os atributos que compõem uma foto de uma planta, permitindo que ela tenha múltiplas imagens'''

    # Relaciona as fotos com a planta
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name= 'photos', verbose_name="Planta")

    # Campo que contém uma imagem e indica a função que retorna onde a imagem deve ser guardada
    image = models.ImageField(upload_to=plant_directory_path, verbose_name="Imagens")

    # Cria um campo não editável que conterá imagens pequenas geradas a partir das imagens maiores 
    small_image = models.ImageField(upload_to=small_plant_directory_path, editable=False, null=True)

    # source_plant_photo = models.CharField('Referência da foto', blank=True, help_text='Insira a referência utilizada', default='Desconhecido', max_length=100)

    published = models.BooleanField(verbose_name="Publicado", null=True)

    def __str__(self):
        return self.image.name

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
            raise ValueError("Imagem da planta {} não contém a dimensão mínima indicada (Full HD: 1920x1080)".format(self.image))

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'