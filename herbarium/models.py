from django.db import models
from PIL import Image, ExifTags
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify

'''
#Create your models here.
class Division(models.Model):
    # Cria divisão de plantas: por Dicotiledôneas e Monocotiledôneas

    # Cria uma variável do tipo texto com máximo de 100 caracteres que pode estar vazio
    # name = models.CharField('Nome', blank=True, max_length=100) (TROCAR BLANK = TRUE)
    name = models.CharField('Nome', blank=False, max_length=50)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.name

    # Configurações do model (Como aparece no admin)
    class Meta:
        verbose_name = 'Divisão'
        verbose_name_plural = 'Divisões'
        ordering = ['name'] #ordena por ordem alfabética
'''

class Region(models.Model):

    name = models.CharField('Região', blank=True, max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'
        ordering = ['name']

class State(models.Model):

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
    # Cria famílias de plantas

    # Cria uma variável do tipo texto com máximo de 100 caracteres
    name = models.CharField('Nome', blank=False, max_length=100)

    # Relação de 1 para muitos entre família e divisão
    # on_delete = se deletar 1 divisão, deleta todas as famílias que são daquela divisão
    # related_name = ObjetivoTipoDivision.families retorna todas as famílias daquela divisao 
    # division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='families')


    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Família'
        verbose_name_plural = 'Famílias'
        ordering = ['name']

class Plant(models.Model):
    # Define o que é uma planta

    #Escolha de família separa por divisão a qual a família pertence.

    # Objetivo: tirar
    '''
    FAMILY_CHOICES = [
        ('Dicotiledôneas' ,
            (
                ('amaranthaceae', 'Amaranthaceae'),
                ('asteraceae', 'Asteraceae'),
                ('brassicaceae', 'Brassicaceae'),
                ('caryophyllaceae', 'Caryophyllaceae'),
                ('cyperaceae', 'Cyperaceae'),
                ('convolvulaceae', 'Convolvulaceae'),
                ('euphobiaceae', 'Euphobiaceae'),
                ('malvaceae', 'Malvaceae'),

            )

        ),

        ('Monocotiledôneas',

            (
                ('plantaginaceae', 'Plantaginaceae'),
                ('poaceae', 'Poaceae'),
                ('polygonaceae', 'Polygonaceae'),
                ('rubiaceae', 'Rubiaceae'),
                ('sapindaceae', 'Sapindaceae'),
                ('solanaceae', 'Solanaceae'),

            )



        )


    ]
    '''

    # Quando plantas forem cadastradas, deverá conter todas as informações a seguir???

    name = models.CharField('Nome', blank=False, max_length=100)
    scientific_name = models.CharField('Nome científico', blank=False, max_length=200)
    complementary_scientific_name = models.CharField(verbose_name="Nome Científico Complementar", max_length=60, blank=True, null=True)

    # MODIFICAR: relacionar a planta com a sua família (classe Family) e com isso, automaticamente, será relacionada com a Division 
    # family = models.CharField('Família', blank=True, max_length=100, choices=FAMILY_CHOICES)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="plants", verbose_name="Família")

    # Objetivo: tirar
    # division = models.CharField("Divisão", blank=True, editable=False, max_length=100)

    # Torna um conjunto de palavras passíveis para serem usadas como um URL
    # O slug não pode ser repetido, logo unique = True
    slug = models.SlugField('Identificador', blank=True, null=True, unique=True)

    description = models.TextField('Descrição', blank=False)

    importance = models.TextField('Importância', blank=False, null=True)

    # occurrence_states = models.ManyToManyField(State, verbose_name="Estados de Ocorrência")
    occurrence_regions = models.ManyToManyField(Region, verbose_name="Regiões de Ocorrência")

    # Usado para fazer imagem 3D
    # fyuseimage = models.TextField('ID imagem do Fyuse', blank=False, max_length=1000)

    created_at = models.DateField('Criado em', auto_now_add=True, null=False)
    updated_at = models.DateField('Criado em', auto_now=True, null=False)

    # Objetivo: tirar
    '''
    def save( self, *args, **kw ):
        #Define a divisão baseado na família selecionada
        family = (self.family, self.family.capitalize()) #para que a tupla fique igual a que está no choices
        if family in  self.FAMILY_CHOICES[0][1]:
            self.division = self.FAMILY_CHOICES[0][0]
        elif family in self.FAMILY_CHOICES[1][1]:
            self.division = self.FAMILY_CHOICES[1][0]
        else:
            self.division = 'Não registrado'

        super( Plant, self ).save( *args, **kw )
    '''

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


# Função que retorna onde imagens grandes devem ser guardadas
def plant_directory_path(instance, filename):

    plant_name = slugify(instance.plant.name)

    return 'plantas/imagens-grandes/{}/{}'.format(plant_name, filename)

# Função que retorna onde imagens pequenas devem ser guardadas
def small_plant_directory_path(instance, filename):

    plant_name = slugify(instance.plant.name)

    return 'plantas/imagens-pequenas/{}/{}'.format(plant_name, filename)

# Função para criar uma imagem miniatura com um tamanho específico (1210x908) a partir de uma imagem maior 
# Usar size=(1210, 908) ou 30% da dimensão?
def make_small_image(image, size=(645, 430)):
    im = Image.open(image) # Abre a imagem com o Pillow

    im.convert('RGB')

    # image_width, image_height = im.size # Define image_width como o primeiro valor da tupla e image_size como segundo

    im.thumbnail(size) # Redimensiona a imagem com o tamanho padrão descrito nos parâmetros

    # im.thumbnail((image_width*0.2, image_height*0.2)) # Redimensiona a imagem para diminuir 70% da dimensão da largura e da altura

    thumb_io = BytesIO() # Cria um objeto BytesIO

    im.save(thumb_io, 'JPEG', quality=100) # Salva imagem para um objeto BytesIO 

    thumbnail = File(thumb_io, name=image.name) # Cria um objeto File 'amigável' ao Django 

    return thumbnail

def remove_metadata(image_with_metadata):
    # PROBLEMA:
    # image = Image.open(image_with_metadata)

    # data = list(image.getdata())

    # # print(data)
    # image_without_exif = Image.new(image.mode, image.size)
    # image_without_exif.putdata(data)

    # image_without_exif.rotate(180)

    # thumb_io = BytesIO() # Cria um objeto BytesIO

    # image_without_exif.save(thumb_io, 'JPEG', quality=100) # Salva imagem para um objeto BytesIO 

    # image_without_metadata = File(thumb_io, name=image_with_metadata.name) # Cria um objeto File 'amigável' ao Django

    # return image_without_metadata

    
    image=Image.open(image_with_metadata)

    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation]=='Orientation':
            break
    
    exif = image._getexif()

    if exif[orientation] == 3:
        image=image.rotate(180, expand=True)
    elif exif[orientation] == 6:
        image=image.rotate(270, expand=True)
    elif exif[orientation] == 8:
        image=image.rotate(90, expand=True)

    thumb_io = BytesIO() # Cria um objeto BytesIO

    image.save(thumb_io, 'JPEG', quality=100)
    # image.close()

    image_rotate = File(thumb_io, name=image_with_metadata.name)
    return image_rotate

#Modelo de foto para que seja possível a planta ter multiplas imagens
class Photo(models.Model):
    # Cria modelo para fotos das plantas

    # Relaciona as fotos com a planta
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name= 'photos')

    # Campo que contém uma imagem e indica a função que retorna onde a imagem deve ser guardada
    image = models.ImageField(upload_to=plant_directory_path, verbose_name="Imagens")

    # Cria um campo não editável que conterá imagens pequenas geradas a partir das imagens maiores 
    small_image = models.ImageField(upload_to=small_plant_directory_path, editable=False, null=True)

    def __str__(self):
        return self.image.name

    # Sobreescreve o método save
    def save(self, *args, **kwargs):
        # Realiza o processamento na imagem cadastrada (self.image) e guarda o retorno no atributo small_image
        pillow_img = Image.open(self.image)

        pillow_img_width, pillow_img_height = pillow_img.size

        # Especificando tamanho mínimo como Full HD
        if (pillow_img_width >= 1920 and pillow_img_height >= 1080) or (pillow_img_width >= 1080 and pillow_img_height >= 1920):
            func = remove_metadata(self.image)
            self.image = func
            # Cria a imagem pequena e insere no campo do modelo            
            self.small_image = make_small_image(self.image)
            super().save(*args, **kwargs)
        else:
            raise ValueError("Imagem da planta {} não contém a dimensão mínima indicada (Full HD: 1920x1080)".format(self.image))

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

