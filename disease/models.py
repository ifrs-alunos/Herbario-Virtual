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
    slug = models.SlugField(blank=True, null=True)
    name = models.CharField('Nome', blank=False, max_length=100)

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

class ConditionSolicitation(models.Model):
    '''Essa classe realiza a solicitação para cadastramento de nova condições'''

    CONDITIONS_KIND_CHOICES = (
        ("int", "Número inteiro"),
        ("float", "Número decimal"),
        ("str", "Texto"),
    )

    condition_name = models.CharField('Nome da condição', max_length=100, blank=False, help_text='Insira o nome da condição')
    condition_kind = models.CharField('Tipo de dado', max_length=5, choices=CONDITIONS_KIND_CHOICES, help_text='Selecione o tipo de dado a ser informado', blank=False)

    # Retorna variável name caso seja dado um print do objeto
    def __str__(self):
        return self.condition_name

    class Meta:
        verbose_name = 'Condição'
        verbose_name_plural = 'Condições'
        ordering = ['condition_name']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]


class Disease(models.Model):
    '''Esta classe define os dados de doença de uma planta. Estes serão catalogados e adicionados ao herbário'''

    name_disease = models.CharField('Nome da doença', blank=False, max_length=100, help_text='Insira o nome da doença')
    scientific_name_disease = models.CharField('Nome científico', blank=False, max_length=200, help_text='Insira o nome científico da doença')
    complementary_scientific_name_disease = models.CharField(verbose_name="Nome Científico Complementar", max_length=60, blank=True, null=True, help_text='Insira o nome científico complementar, caso houver')

    # Torna um conjunto de palavras passíveis para serem usadas como um URL
    slug = models.SlugField('Identificador', blank=True, null=True, unique=True)

    # Informações relacionados à doença, sintomas, plantas afetadas, etc
    culture_disease = models.ForeignKey(Culture, on_delete=models.CASCADE, related_name="cultures", verbose_name="Cultura", help_text='Insira a cultura de lavoura afetada')
    symptoms_disease = models.TextField('Sintomas', blank=False, help_text='Insira uma descrição sobre os sintomas da doença')
    cycle_disease = models.TextField('Ciclo da doença', blank=True, help_text='Descreva o ciclo da doença')
    # hostesses_plants_disease = models.TextField('Plantas hospedeiras da doença', blank=False, help_text='Insira as plantas hospedeiras desta doença')
    occurrence_regions_disease = models.ManyToManyField(Region, verbose_name="Regiões de Ocorrência", help_text='Selecione as regiões de ocorrência desta doença')
    management_disease = models.TextField('Medidas de controle', blank = True, help_text = 'Descreva as medidas para controle desta doença')
    source_disease = models.TextField('Referências', blank = False, help_text = 'Insira as referências utilizadas')

    # Informações relacionadas às condições para desenvolvimento da doença
    # conditions = models.OneToOneField(
    #     Conditions,
    #     verbose_name="Condições para ocorrência",
    #     help_text="Insira as condições para ocorrência",
    #     on_delete=models.CASCADE,
    #     default=0,
    #     primary_key=True,
    # )

    # Dados relacionados à criação e publicação de atualizações
    created_at_disease = models.DateField('Criado em', auto_now_add=True, null=False)
    updated_at_disease = models.DateField('Atualizado em', auto_now=True, null=False)

    # Booleando representando o estado de publicação desta doença
    published_disease = models.BooleanField(verbose_name="Publicado", null=True)

    def __str__(self):
        return self.name_disease

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.name_disease)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Doença'
        verbose_name_plural = 'Doenças'
        ordering = ['name_disease']
        permissions = [('contribute_with_disease', 'Pode contribuir com doenças')]






