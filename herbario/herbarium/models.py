from django.db import models

#Create your models here.
class Division(models.Model):

    name = models.CharField('Nome', blank=True, max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Divisão'
        verbose_name_plural = 'Divisões'
        ordering = ['name']


class Family(models.Model):

    name = models.CharField('Nome', blank=True, max_length=100)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='families')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Família'
        verbose_name_plural = 'Famílias'
        ordering = ['name']


class Plant(models.Model):

    #Escolha de família separa por divisão a qual a família pertence.
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




    name = models.CharField('Nome', blank=True, max_length=100)
    scientific_name = models.CharField('Nome científico', blank=True, max_length=200)


    family = models.CharField('Família', blank=True, max_length=100, choices=FAMILY_CHOICES)
    division = models.CharField("Divisão", blank=True, editable=False, max_length=100)
    slug = models.SlugField('Identificador', blank=True, null=True)
    description = models.TextField('Descrição', blank=True)


    created_at = models.DateField('Criado em', auto_now_add=True, null=True)
    updated_at = models.DateField('Criado em', auto_now=True, null=True)

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


    def __str__(self):

        return self.name

    class Meta:
        verbose_name = 'Planta'
        verbose_name_plural = 'Plantas'
        ordering = ['name']


def plant_directory_path(instance, filename):

    return 'images/plantas/{}/{}'.format(instance.plant.name, filename)


#Modelo de foto para que seja possível a planta ter multiplas Imagens

class Photo(models.Model):

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name= 'photos' )
    image = models.ImageField(upload_to= plant_directory_path )

    def __str__(self):

        return self.image.name

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'
