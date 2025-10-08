from django.db import models
from django.utils.text import slugify


class Family(models.Model):
    """Esta classe define uma família de uma planta"""

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
