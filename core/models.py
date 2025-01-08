from PIL import Image
from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from bs4 import BeautifulSoup

from core.utils import make_small_image


def highlight_directory_path(instance, filename):
	# Transforma a string passada como parâmetro em um slug
	folder_name = slugify(instance.title)

	return 'destaques/noticias/{}/{}'.format(folder_name, filename)

class Highlight(models.Model):
	"""Essa classe define um destaque que será exibido na página inicial"""

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
	"""Retorna o diretório onde são armazenadas as imagens do carossel da página inicial"""

	image_order = slugify(instance.list_order)
	image_title = slugify(instance.title)

	return 'destaques/carrossel/slide {}/{}/{}'.format(image_order, image_title, filename)


class CarouselImage(models.Model):
	"""Essa classe define os atributos de uma imagem que é exibida no carrossel da página inicial"""

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
	"""Essa classe define os atributos de um colaborador do projeto"""

	year = models.IntegerField('Ano de início do projeto', blank=True, default=0,
							   help_text='Insira o ano de início do projeto')
	name_project = models.CharField('Nome do projeto', blank=True, max_length=200, help_text='Insira o nome do projeto')
	student_name = models.CharField('Nome do(s) bolsista(s)', blank=True, max_length=300,
									help_text='Ins        ira o nome do(s) bolsista(s) do projeto')
	advisor_name = models.CharField('Nome do(s) orientador(es)', blank=True, max_length=200,
									help_text='Insira o nome do(s) orientador(es) do projeto')
	co_advisor_name = models.CharField('Nome do(s) coorientador(es)', max_length=400, blank=True,
									   help_text='Insira o nome do(s) coorientador(es) do projeto')

	class Meta:
		verbose_name = 'Colaboradores'
		verbose_name_plural = 'Colaboradores do projeto'
		ordering = ['year']


class Content(models.Model):
	"""Essa classe define o conteúdo de um livro"""

	name = models.CharField('Nome', max_length=400, )
	slug = models.SlugField('Identificador', blank=True, null=True, max_length=255)

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if self.slug is None:
			self.slug = slugify(self.name)

		super().save(*args, **kwargs)

	class Meta:
		verbose_name = 'Conteúdo'
		verbose_name_plural = 'Conteúdos'


class Book(models.Model):
	"""Essa classe define os atributos de um livro"""

	name = models.CharField('Nome', max_length=400, )
	link = models.URLField('Link', max_length=400)
	content = models.ForeignKey(Content, on_delete=models.CASCADE, verbose_name="Cultura")

	def __str__(self):
		return f'{self.name} - {self.content}'

	class Meta:
		verbose_name = 'Livro'
		verbose_name_plural = 'Livros'


class Publication(models.Model):
	"""Esta classe define os atributos que compõem uma publicação"""

	title = models.CharField('Título', max_length=100)

	content = HTMLField('Conteúdo', )

	slug = models.SlugField(verbose_name="Slug", unique=True, null=True, blank=True, max_length=255)

	posted_at = models.DateTimeField('Postado em', auto_now_add=True, null=False)

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		if self.slug == None:
			self.slug = slugify(self.title)

		super().save(*args, **kwargs)

	@property
	def get_content_preview(self):
		try:
			soup = BeautifulSoup(self.content, 'html.parser')
			return soup.find('p').getText()
		except AttributeError as e:
			return 'Erro ao carregar prévia do conteúdo'

	class Meta:
		verbose_name = 'Publicação'
		verbose_name_plural = 'Publicações'
		ordering = ('-posted_at',)


def publication_directory_path(instance, filename):
	"""Esta função retorna o diretório onde as imagens grandes de uma publicação devem ser armazenadas"""

	publication_name = slugify({instance.publication.title})

	return 'publicacoes/imagens-grandes/{}/{}'.format(publication_name, filename)


def small_publication_directory_path(instance, filename):
	"""Esta função retorna o diretório onde as imagens pequenas de uma publicação devem ser armazenadas"""

	publication_name = slugify({instance.publication.title})

	# Arruma um pequeno bug de redundancia de path
	filename = filename.split('/')[-1]

	return 'publicacoes/imagens-pequenas/{}/{}'.format(publication_name, filename)


class PhotoPublication(models.Model):
	"""Esta classe define os atributos que compõem uma foto de uma publicação, permitindo que ela tenha múltiplas
	imagens"""

	# Relaciona as fotos com a publicação
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='photos',
									verbose_name="Publicação")

	# Campo que contém uma imagem e indica a função que retorna onde a imagem deve ser guardada
	image = models.ImageField(upload_to=publication_directory_path, verbose_name="Imagens", max_length=500)

	# Cria um campo não editável que conterá imagens pequenas geradas a partir das imagens maiores
	small_image = models.ImageField(upload_to=small_publication_directory_path, editable=False, null=True,
									max_length=500)

	def __str__(self):
		return self.image.name

	def save(self, *args, **kwargs):
		# Realiza o processamento na imagem cadastrada (self.image) e guarda o retorno no atributo small_image
		pillow_img = Image.open(self.image)

		pillow_img_width, pillow_img_height = pillow_img.size
		self.small_image = make_small_image(self.image)
		super().save(*args, **kwargs)

	class Meta:
		verbose_name = 'Foto da publicação'
		verbose_name_plural = 'Fotos das plublicações'
