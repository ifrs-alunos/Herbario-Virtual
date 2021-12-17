from django.db import models
from django.utils.text import slugify


class CharSolicitationModel(models.Model):
    """Essa classe define uma solicitação de uma condição para desenvolvimento por um contribuidor"""

    CHAR_KIND_CHOICES = (
        ("float", "Número"),
        ("str", "Texto"),
        ("boolean", "Condicional")
    )

    CHAR_RELATIONALS_CHOICES = (
        (">", "Maior"),
        (">=", "Maior ou igual"),
        ("!=", "Diferente"),
        ("==", "Igual"),
        ("<", "Menor"),
        ("<=", "Menor ou igual"),
    )

    char_name = models.CharField('Nome da característica', max_length=100, blank=False, help_text='Insira o nome da característica')
    char_kind = models.CharField('Tipo de dado', max_length=10, choices=CHAR_KIND_CHOICES, help_text='Selecione o tipo de dado a ser informado', blank=False)
    char_relationals = models.CharField('Comparativos/relacionais', max_length=25, choices=CHAR_RELATIONALS_CHOICES, help_text='Selecione a expressão correspondente para ocorrência da doença. Exemplificação: para ocorrência de doença X a temperatura deve ser menor que a tempratura mínima.', blank=False)
    char_tolerance = models.FloatField('Valor de tolerância/margem de erro', null=True, blank=True, help_text='Insira um valor de tolerância/margem de erro')
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

    def get_html_input(self):
        if self.char_kind == 'float':
            return '<input class="form-control" name="charval" type="number" step="0.01">'
        elif self.char_kind == 'str':
            return '<input class="form-control" name="charval" type="text">'
        else:
            return '<select name="charval" class="select form-control"><option value="1">Verdadeiro</option><option value="0">Falso</option></select>'