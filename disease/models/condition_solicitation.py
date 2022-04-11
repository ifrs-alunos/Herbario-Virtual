from django.db import models


class ConditionSolicitation(models.Model):
    '''Essa classe realiza a solicitação para cadastramento de nova condições'''

    CONDITIONS_KIND_CHOICES = (
        ("int", "Número inteiro"),
        ("float", "Número decimal"),
        ("str", "Texto"),
    )

    condition_name = models.CharField('Nome da condição', max_length=100, blank=False,
                                      help_text='Insira o nome da condição')
    condition_kind = models.CharField('Tipo de dado', max_length=5, choices=CONDITIONS_KIND_CHOICES,
                                      help_text='Selecione o tipo de dado a ser informado', blank=False)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.condition_name

    class Meta:
        verbose_name = 'Condição'
        verbose_name_plural = 'Condições'
        ordering = ['condition_name']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]
