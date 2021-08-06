from django.db import models
from django.utils.text import slugify

class Region(models.Model):
    '''Esta classe define uma região de um país'''

    name = models.CharField('Região', blank=True, max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'
        # ordering = ['name_disease']

class State(models.Model):
    '''Esta classe define um estado (unidade federativa) que pertence à uma região'''

    name = models.CharField('Nome', blank=False, max_length=20)
    initials = models.CharField('Sigla', blank=False, max_length=2, null=True)

    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="states", null=True, verbose_name="Região")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        # ordering = ['name_disease']

class Culture(models.Model):
    '''Esta classe define a cultura da lavoura'''

    # Cria uma variável do tipo texto com máximo de 100 caracteres
    name = models.CharField('Nome', blank=False, max_length=100)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Cultura'
        verbose_name_plural = 'Culturas'
        ordering = ['name']

class Conditions(models.Model):
    '''Essa classe define as condições necessárias para desenvolvimento de uma determinada doença'''

    disease_name = models.CharField('Nome da doença', max_length=100, blank=False, help_text='Insira o nome da doença')
    minimum_temperature = models.FloatField('Temperatura mínima', blank=True, help_text='Insira a temperatura mínima para desenvolvimento', default=0)
    maximum_temperature = models.FloatField('Temperatura máxima', blank=True, help_text='Insira a temperatura máxima para desenvolvimento', default=0)
    humidity = models.FloatField('Umidade', blank=True, help_text='Insira a umidade relativa do ar para ocorrência da doença', default=0)
    pression = models.FloatField('Pressão', blank=True, help_text='Insira a pressão para ocorrência da doença', default=0)
    altitude = models.FloatField('Altitude', blank=True, help_text='Insira a altitude para ocorrência da doença', default=0)
    close_occurrence = models.BooleanField('Ocorrência desta doença na localidade', blank=True, help_text='Assinale caso a ocorrência da doença na localidade seja um requisito para desenvolvimento desta', default=False)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.disease_name

    class Meta:
        verbose_name = 'Condições'


class Disease(models.Model):
    '''Esta classe define os dados de doença de uma planta. Estes serão catalogados e adicionados ao herbário'''

    name_disease = models.CharField('Nome da doença', blank=False, max_length=100, help_text='Insira o nome da doença')
    scientific_name_disease = models.CharField('Nome científico', blank=False, max_length=200, help_text='Insira o nome científico da doença')
    complementary_scientific_name_disease = models.CharField(verbose_name="Nome Científico Complementar", max_length=60, blank=True, null=True, help_text='Insira o nome científico complementar, caso houver')

    # Torna um conjunto de palavras passíveis para serem usadas como um URL
    slug_disease = models.SlugField('Identificador', blank=True, null=True, unique=True)

    # Informações relacionados à doença, sintomas, plantas afetadas, etc
    culture_disease = models.ForeignKey(Culture, on_delete=models.CASCADE, related_name="cultures", verbose_name="Cultura", help_text='Insira a cultura de lavoura afetada')
    symptoms_disease = models.TextField('Sintomas', blank=False, help_text='Insira uma descrição sobre os sintomas da doença')
    # hostesses_plants_disease = models.TextField('Plantas hospedeiras da doença', blank=False, help_text='Insira as plantas hospedeiras desta doença')
    occurrence_regions_disease = models.ManyToManyField(Region, verbose_name="Regiões de Ocorrência", help_text='Selecione as regiões de ocorrência desta doença')
    taxonomy_disease = models.TextField('Taxonomia', blank = False, help_text = 'Descreva a taxonomia desta doença')
    management_disease = models.TextField('Manejo', blank = False, help_text = 'Descreva o manejo desta doença')
    source_disease = models.TextField('Referências', blank = False, help_text = 'Insira as referências utilizadas')

    conditions = models.OneToOneField(
        Conditions,
        verbose_name="Condições para ocorrência",
        help_text="Insira as condições para ocorrência",
        on_delete=models.CASCADE,
        default=0,
        primary_key=True,
    )

    # Dados relacionados à criação e publicação de atualizações
    created_at_disease = models.DateField('Criado em', auto_now_add=True, null=False)
    updated_at_disease = models.DateField('Criado em', auto_now=True, null=False)

    # Booleando representando o estado de publicação desta doença
    published_disease = models.BooleanField(verbose_name="Publicado", null=True)

    def __str__(self):
        return self.name_disease

    def save(self, *args, **kwargs):
        if self.slug_disease == None:
            self.slug_disease = slugify(self.name_disease)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Doença'
        verbose_name_plural = 'Doenças'
        ordering = ['name_disease']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]






