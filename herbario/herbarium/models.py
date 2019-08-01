from django.db import models

# Create your models here.

class Plant(models.Model):

    FAMILY_CHOICES = [


    ]

    PLANT_CLASS_CHOICES = [
        ('Gramosa', 'gramosa'),
        ('Abacaxium', 'abacaxium'),
        ('matinhum', 'matinhum'),
    ]

    ORDER_CHOICES = []

    DIVISION_CHOICES = []


    name = models.CharField('Nome', blank=True, max_length=100)
    scientific_name = models.CharField('Nome científico', blank=True, max_length=200)

    plant_class = models.CharField('Classe', blank=True, max_length=100, choices=PLANT_CLASS_CHOICES)
    family = models.CharField('Família', blank=True, max_length=100, choices=FAMILY_CHOICES)
    order = models.CharField('Ordem', blank=True, max_length=100, choices=ORDER_CHOICES)
    division = models.CharField('Divisão', blank=True, max_length=100, choices=DIVISION_CHOICES)

    slug = models.SlugField('Identificador', blank=True, null=True)
    image = models.ImageField('Imagem',upload_to='images', blank=True)
    description = models.TextField('Descrição', blank=True)


    created_at = models.DateField('Criado em', auto_now_add=True, null=True)
    updated_at = models.DateField('Criado em', auto_now=True, null=True)

    def __str__(self):

        return self.name

    class Meta:
        verbose_name = 'Planta'
        verbose_name_plural = 'Plantas'
        ordering = ['name']
