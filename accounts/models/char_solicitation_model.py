from django.db import models
from django.utils.text import slugify

class CharSolicitationModel(models.Model):
    """Essa classe define uma solicitação de uma condição para desenvolvimento por um contribuidor"""

    CONDITIONS_KIND_CHOICES = (
        ("float", "Número"),
        ("str", "Texto"),
        ("boolean", "Condicional")
    )

    char_name = models.CharField('Nome da característica', max_length=100, blank=False, help_text='Insira o nome da característica')
    char_kind = models.CharField('Tipo de dado', max_length=10, choices=CONDITIONS_KIND_CHOICES, help_text='Selecione o tipo de dado a ser informado', blank=False)

    # validated = models.BooleanField(default=False, verbose_name="Validado")

    # Torna um conjunto de palavras passíveis para serem usadas como um URL
    slug = models.SlugField('Identificador', blank=True, null=True, unique=True)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.char_name

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.char_name)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Solicitação de característica'
        verbose_name_plural = 'Solicitações de características'
        ordering = ['char_name']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]
