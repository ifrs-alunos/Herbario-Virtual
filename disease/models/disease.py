from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.text import slugify

from disease.models import Culture, Region


class Disease(models.Model):
    """Esta classe define os dados de doença de uma planta. Estes serão catalogados e adicionados ao herbário"""

    name_disease = models.CharField('Nome da doença', blank=False, max_length=100, help_text='Insira o nome da doença')
    scientific_name_disease = models.CharField('Nome científico', blank=False, max_length=200,
                                               help_text='Insira o nome científico da doença')
    complementary_scientific_name_disease = models.CharField(verbose_name="Nome Científico Complementar", max_length=60,
                                                             blank=True, null=True,
                                                             help_text='Insira o nome científico complementar, caso houver')

    # Torna um conjunto de palavras passíveis para serem usadas como um URL
    slug = models.SlugField('Identificador', blank=True, null=True, unique=False, max_length=255)

    # Informações relacionados à doença, sintomas, plantas afetadas, etc
    culture_disease = models.ForeignKey(Culture, on_delete=models.CASCADE, related_name="cultures",
                                        verbose_name="Cultura", help_text='Insira a cultura de lavoura afetada')
    symptoms_disease = models.TextField('Sintomas', blank=False,
                                        help_text='Insira uma descrição sobre os sintomas da doença')
    cycle_disease = models.TextField('Ciclo da doença', blank=True, help_text='Descreva o ciclo da doença')
    occurrence_regions_disease = models.ManyToManyField(Region, blank=True,
                                                        verbose_name="Regiões de Ocorrência",
                                                        help_text='Selecione as regiões de ocorrência desta doença')
    management_disease = models.TextField('Medidas de controle', blank=True,
                                          help_text='Descreva as medidas para controle desta doença')
    environmental_conditions_disease = models.TextField('Condições ambientais de desenvolvimento', blank=True,
                                              help_text='Insira as condições ambientais de desenvolvimento')
    references_disease = models.TextField('Referências', blank=True,null=True, help_text='Insira as referências utilizadas')

    # Estados em que a planta pode aparecer nas imagens de treino do modelo de IA.
    # Cada doença tem os seus: a ferrugem asiática da soja, por exemplo, tem só
    # "doente" e "saudável". Quem aprova uma imagem escolhe um deles (ver
    # telegram_bot.services.approve_training_photo).
    states = ArrayField(
        models.CharField(max_length=60),
        default=list,
        blank=True,
        verbose_name='Estados da doença',
        help_text='Separados por vírgula. Ex.: doente,saudável',
    )

    # Dados relacionados à criação e publicação de atualizações
    created_at_disease = models.DateField('Criado em', auto_now_add=True, null=False)
    updated_at_disease = models.DateField('Atualizado em', auto_now=True, null=False)

    # Booleando representando o estado de publicação desta doença
    published_disease = models.BooleanField(verbose_name="Publicado", null=True)

    def __str__(self):
        return self.name_disease

    @property
    def published_photos(self):
        """Fotos aprovadas por um administrador — as únicas que o site público exibe.

        Virou `property` para casar com Plant.published_photos: como método, o
        template chamava sozinho mas o Python devolvia a função. Os templates
        continuam iguais.
        """

        return self.photos.filter(published=True)

    def add_state(self, name):
        """Acrescenta um estado à lista, se ainda não houver um de mesmo nome.

        Devolve o nome como ficou gravado: digitar "Doente" quando já existe
        "doente" reaproveita o existente.
        """

        name = name.strip()
        for existente in self.states:
            if existente.lower() == name.lower():
                return existente

        self.states = self.states + [name]
        self.save(update_fields=['states'])
        return name

    def save(self, *args, **kwargs):
        # Sem espaços nas pontas e sem itens vazios ("doente, ,saudável")
        self.states = [state.strip() for state in self.states if state and state.strip()]

        if self.slug is None:
            self.slug = slugify(self.name_disease)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Doença'
        verbose_name_plural = 'Doenças'
        ordering = ['name_disease']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]
