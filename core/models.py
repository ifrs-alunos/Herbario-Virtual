from django.db import models
from django.utils.text import slugify

# Create your models here.

def highlight_directory_path(instance, filename):

    # Transforma a string passada como parâmetro em um slug
    folder_name = slugify(instance.title)

    return 'destaques/noticias/{}/{}'.format(folder_name, filename)

'''
def more_highlight_path(instance, filename):

    # Transforma a string passada como parâmetro em um slug
    folder_name = slugify(instance.title)

    return 'destaques/noticias/{}/mais-imagens/{}'.format(folder_name, filename)
'''

class Highlight(models.Model):
    # keyword = models.CharField('Palavra-chave', blank=False, max_length=10, null=True)

    title = models.CharField('Título', blank=False, max_length=50)

    text = models.TextField('Texto', blank=False)

    image = models.ImageField('Imagem', upload_to=highlight_directory_path)

    slug = models.SlugField(verbose_name="Slug", unique=True, null=True, blank=True)

    more_information = models.TextField(verbose_name='Mais Informações', null=True)

    # more_photos = models.ImageField(verbose_name='Mais Imagens', upload_to=more_highlight_path)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.title)
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Destaque'
        verbose_name_plural = 'Destaques'
        ordering = ['id']

def carousel_image_directory_path(instance, filename):
    
    image_order = slugify(instance.list_order)
    image_title = slugify(instance.title)

    return 'destaques/carrossel/slide {}/{}/{}'.format(image_order, image_title, filename)

class CarouselImage(models.Model):

    title = models.CharField('Título', max_length=25, blank=False, null=True)

    description = models.CharField('Descrição Rápida', max_length=60, blank=False, null=True)

    image = models.ImageField('Imagem', upload_to=carousel_image_directory_path, blank=False)

    list_order = models.IntegerField('Ordem no Carrossel', blank=False, null=True, unique=True) 

    def __str__(self):
        return "Slide {}: {}".format(self.list_order, self.title)

    class Meta:
        verbose_name = 'Imagem do Carrossel'
        verbose_name_plural = 'Imagens do Carrossel'
        ordering = ['list_order']

class Colaborators(models.Model):

    year = models.IntegerField('Ano de início do projeto', blank=True, default=0, help_text='Insira o ano de início do projeto')
    name_project = models.CharField('Nome do projeto', blank=True, max_length=100, help_text='Insira o nome do projeto')
    student_name = models.CharField('Nome do(s) bolsista(s)', blank=True, max_length=200, help_text='Insira o nome do(s) bolsista(s) do projeto')
    advisor_name = models.CharField('Nome do(s) orientador(es)', blank=True, max_length=200, help_text='Insira o nome do(s) orientador(es) do projeto')
    co_advisor_name = models.CharField('Nome do(s) coorientador(es)', max_length=300, blank=True, help_text='Insira o nome do(s) coorientador(es) do projeto')

    class Meta:
        verbose_name = 'Colaboradores'
        verbose_name_plural = 'Colaboradores do projeto'
        ordering = ['year']