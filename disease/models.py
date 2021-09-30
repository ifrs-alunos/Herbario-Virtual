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
        # ordering = ['name_disease']

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
        # ordering = ['name_disease']

class Culture(models.Model):
    '''Esta classe define a cultura da lavoura'''

    # Cria uma variável do tipo texto com máximo de 100 caracteres
    slug = models.SlugField(blank=True, null=True)
    name = models.CharField('Nome da cultura', blank=False, max_length=100, help_text='Digite o nome da cultura')

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.name

    def save(self):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save()

    class Meta:
        verbose_name = 'Cultura'
        verbose_name_plural = 'Culturas'
        ordering = ['name']

class ConditionSolicitation(models.Model):
    '''Essa classe realiza a solicitação para cadastramento de nova condições'''

    CONDITIONS_KIND_CHOICES = (
        ("int", "Número inteiro"),
        ("float", "Número decimal"),
        ("str", "Texto"),
    )

    condition_name = models.CharField('Nome da condição', max_length=100, blank=False, help_text='Insira o nome da condição')
    condition_kind = models.CharField('Tipo de dado', max_length=5, choices=CONDITIONS_KIND_CHOICES, help_text='Selecione o tipo de dado a ser informado', blank=False)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.condition_name

    class Meta:
        verbose_name = 'Condição'
        verbose_name_plural = 'Condições'
        ordering = ['condition_name']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]


class Disease(models.Model):
    '''Esta classe define os dados de doença de uma planta. Estes serão catalogados e adicionados ao herbário'''

    name_disease = models.CharField('Nome da doença', blank=False, max_length=100, help_text='Insira o nome da doença')
    scientific_name_disease = models.CharField('Nome científico', blank=False, max_length=200, help_text='Insira o nome científico da doença')
    complementary_scientific_name_disease = models.CharField(verbose_name="Nome Científico Complementar", max_length=60, blank=True, null=True, help_text='Insira o nome científico complementar, caso houver')

    # Torna um conjunto de palavras passíveis para serem usadas como um URL
    slug = models.SlugField('Identificador', blank=True, null=True, unique=True)

    # Informações relacionados à doença, sintomas, plantas afetadas, etc
    culture_disease = models.ForeignKey(Culture, on_delete=models.CASCADE, related_name="cultures", verbose_name="Cultura", help_text='Insira a cultura de lavoura afetada')
    symptoms_disease = models.TextField('Sintomas', blank=False, help_text='Insira uma descrição sobre os sintomas da doença')
    cycle_disease = models.TextField('Ciclo da doença', blank=True, help_text='Descreva o ciclo da doença')
    occurrence_regions_disease = models.ManyToManyField(Region, verbose_name="Regiões de Ocorrência", help_text='Selecione as regiões de ocorrência desta doença')
    management_disease = models.TextField('Medidas de controle', blank = True, help_text = 'Descreva as medidas para controle desta doença')
    source_disease = models.TextField('Referências', blank = False, help_text = 'Insira as referências utilizadas')

    # Dados relacionados à criação e publicação de atualizações
    created_at_disease = models.DateField('Criado em', auto_now_add=True, null=False)
    updated_at_disease = models.DateField('Atualizado em', auto_now=True, null=False)

    # Booleando representando o estado de publicação desta doença
    published_disease = models.BooleanField(verbose_name="Publicado", null=True)

    characteristic = models.ForeignKey("accounts.CharSolicitationModel", blank=True, null=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name_disease

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.name_disease)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Doença'
        verbose_name_plural = 'Doenças'
        ordering = ['name_disease']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]


def disease_directory_path(instance, filename):
    '''Esta função retorna o diretório onde as imagens grandes de uma planta devem ser armazenadas'''

    disease_name = slugify(instance.disease.name_disease)

    return 'doencas/imagens-grandes/{}/{}'.format(disease_name, filename)

def small_disease_directory_path(instance, filename):
    '''Esta função retorna o diretório onde as imagens pequenas de uma planta devem ser armazenadas'''

    disease_name = slugify(instance.disease.name_disease)

    return 'doencas/imagens-pequenas/{}/{}'.format(disease_name, filename)

def make_small_image(image, size=(854, 480)):
    '''Esta função retorna uma imagem miniatura com um tamanho específico a partir de uma imagem maior'''

    im = Image.open(image) # Abre a imagem com o Pillow

    im.convert('RGB')

    im.thumbnail(size) # Redimensiona a imagem com o tamanho padrão descrito nos parâmetros

    thumb_io = BytesIO() # Cria um objeto BytesIO

    im.save(thumb_io, 'JPEG', quality=100) # Salva imagem para um objeto BytesIO

    thumbnail = File(thumb_io, name=image.name) # Cria um objeto File 'amigável' ao Django

    return thumbnail

class PhotoDisease(models.Model):
    '''Esta classe define os atributos que compõem uma foto de uma planta, permitindo que ela tenha múltiplas imagens'''

    # Relaciona as fotos com a planta
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name= 'photos', verbose_name="Doença")

    # Campo que contém uma imagem e indica a função que retorna onde a imagem deve ser guardada
    image = models.ImageField(upload_to=disease_directory_path, verbose_name="Imagens")

    # Cria um campo não editável que conterá imagens pequenas geradas a partir das imagens maiores
    small_image = models.ImageField(upload_to=small_disease_directory_path, editable=False, null=True)

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
            raise ValueError("Imagem da doença {} não contém a dimensão mínima indicada (Full HD: 1920x1080)".format(self.image))

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

class Condition(models.Model):
    '''Esta classe define os dados de uma condição de uma doença.'''

    characteristic = models.ForeignKey("accounts.CharSolicitationModel", null=True, on_delete=models.CASCADE)
    float_value = models.FloatField(blank=True, null=True)
    str_value = models.CharField(blank=True, null=True, max_length=100)
    bool_value = models.BooleanField(blank=True, null=True)

    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)

    def value(self):
        if self.characteristic.char_kind == 'float':
            return self.float_value
        elif self.characteristic.char_kind == 'str':
            return self.str_value
        else:
            return  self.bool_value

    def set_value(self, value):
        if self.characteristic.char_kind == 'float':
            self.float_value = value
        elif self.characteristic.char_kind == 'str':
            self.str_value = value
        else:
            self.bool_value = value
        self.save()