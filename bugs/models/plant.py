from django.db import models
from django.utils.text import slugify
from .region import Region
from .family import Family


class Plant(models.Model):
    """Esta classe define uma planta cujas informações serão utilizadas em um herbário virtual"""

    name = models.CharField('Nome', blank=False, max_length=100)
    scientific_name = models.CharField('Nome científico', blank=False, max_length=200)
    complementary_scientific_name = models.CharField(verbose_name="Nome Científico Complementar", max_length=60,
                                                     blank=True, null=True)

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
