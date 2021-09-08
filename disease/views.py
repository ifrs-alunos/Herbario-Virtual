from django.shortcuts import render
from .models import *
from django.views.generic import ListView, DetailView
from .forms import SearchForm

class DiseaseIndex(ListView):
    model = Disease
    template_name = 'index.html'
    context_object_name = 'diseases'

    paginate_by = 6

    # Funcionalidade adicional: lista famílias de plantas ao sobreescrever método get_context_data
    def get_context_data(self, **kwargs):
        # Pega contextos prévios da superclasse (ListView)
        context = super().get_context_data(**kwargs)

        # Adiciona um contexto novo, o qual pega todos os objetos do tipo Culture
        context["cultures"] = Culture.objects.all()
        context["selected_culture"] = self.kwargs.get("culture")

        context["search_form"] = SearchForm(self.request.GET)

        # Retorna o contexto
        return context

    def get_queryset(self, **kwargs):
        # Seleciona todas as plantas

        diseases = Disease.objects.all()
        diseases = diseases.filter(published_disease=True)

        # Executa se alguma família tiver sido selecionada
        if self.kwargs:

            # Filtra todas as plantas por uma família passada na chave 'family' do dicionário da requisição
            diseases = diseases.filter(culture__slug=self.kwargs['culture'])

        # Executa se algum texto tiver sido pesquisado
        if self.request.GET:

            # Instanciando formulário com dados GET da requisição
            search_form = SearchForm(self.request.GET)

            if search_form.is_valid():
                # Acessa o valor do campo text do formulário
                filter_text = search_form.cleaned_data['text']

                # Cria o filtro genérico
                filter = Q(name_disease__icontains=filter_text) | Q(scientific_name_disease__icontains=filter_text) | Q(symptoms_disease__icontains=filter_text)

                # Filtra plantas pelo filtro de texto
                diseases = diseases.filter(filter)

        # Retorna a variável que armazena todas as plantas requisitadas pelo usuário (com ou sem filtro)
        return diseases
