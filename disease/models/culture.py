from django.db import models
from django.utils.text import slugify


def culture_icon_directory_path(instance, filename):
    '''Esta função retorna o diretório onde os icones de uma cultura deve ser armazenada'''

    return 'culturas/icones/{}/{}'.format(instance.slug, filename)


class Culture(models.Model):
    '''Esta classe define a cultura da lavoura'''

    # Cria uma variável do tipo texto com máximo de 100 caracteres
    slug = models.SlugField(blank=True, null=True)
    name = models.CharField('Nome da cultura', blank=False, max_length=100, help_text='Digite o nome da cultura')
    icon = models.FileField(upload_to=culture_icon_directory_path, verbose_name="Icone", blank=True, null=True)

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
