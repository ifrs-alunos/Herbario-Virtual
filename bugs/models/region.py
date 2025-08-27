from django.db import models


class Region(models.Model):
    """Esta classe define uma região de um país"""

    name = models.CharField('Região', blank=True, max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'
        ordering = ['name']
