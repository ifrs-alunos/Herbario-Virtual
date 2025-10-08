from django.shortcuts import render
from django.views.generic import ListView,  DetailView, TemplateView
from django.db.models import Q

from .models import Plant, Family, State
from .forms import SearchForm



# Lista os insetos cadastradas
class bugsIndex(ListView):
    model = Plant
    template_name = 'bugs/index.html'
    context_object_name = 'plants'

    paginate_by = 6

    # Funcionalidade adicional: lista famílias de insetos ao sobreescrever método get_context_data
    def get_context_data(self, **kwargs):
        # Pega contextos prévios da superclasse (ListView)
        context = super().get_context_data(**kwargs)

        # Adiciona um contexto novo, o qual pega todos os objetos do tipo Family
        context["families"] = Family.objects.all()
        context["selected_family"] = self.kwargs.get("family")

        context["search_form"] = SearchForm(self.request.GET)

        # context["families1"] = Family.objects.filter(division__name="Monocotiledôneas")
        # context["families2"] = Family.objects.filter(division__name="Dicotiledôneas")

        # Retorna o contexto
        return context

    def get_queryset(self, **kwargs):
        # Seleciona todos os insetos
        plants = Plant.objects.all()
        plants = plants.filter(published=True)

        if self.kwargs:
            # Filtra todas as plantas por uma família passada na chave 'family' do dicionário da requisição
            # plants = plants.filter(family__name=self.kwargs['family'])
            # Filtra todas as plantas por uma família com o slug passada na chave 'family' do dicionário da requisição
            plants = plants.filter(family__name__iexact=self.kwargs['family'])
        # Executa se algum texto tiver sido pesquisado
        if self.request.GET:
            # Instanciando formulário com dados GET da requisição
            search_form = SearchForm(self.request.GET)

            if search_form.is_valid():
                # Acessa o valor do campo text do formulário
                filter_text = search_form.cleaned_data['text']
                # Cria o filtro genérico
                filter = Q(name__icontains=filter_text) | Q(scientific_name__icontains=filter_text) | Q(description__icontains=filter_text)

                # Filtra plantas pelo filtro de texto
                plants = plants.filter(filter)
                # Executa se alguma família tiver sido selecionada


        # Retorna a variável que armazena todas as plantas requisitadas pelo usuário (com ou sem filtro)
        return plants

class bugsDetail(DetailView):
    # Mostra detalhes de uma planta em específico. Passa no contexto os dados de UMA planta
    model = Plant
    template_name = 'bugs/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Teste pra fazer: adiciona a sigla dos estados
        # context["initials"] = State.objects.all()

        return context

# index = HerbariumIndex.as_view();
# detail = HerbariumDetail.as_view();
