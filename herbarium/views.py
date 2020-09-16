from django.shortcuts import render
from django.views.generic import ListView,  DetailView

from .models import Plant
from .forms import SearchForm

# Create your views here.


# Lista as plantas cadastradas???
class HerbariumIndex(ListView):
    model = Plant
    template_name = 'herbarium/index.html'

    paginate_by = 10
    
    # Pegando Queryset - retorno de um conjunto de busca do banco de dados
    def get_queryset(self): # Reescrevendo um método padrão do Django, que a principio pegaria todas as plantas
        # Pega todas as plantas e faz um filtro

        # Pega as plantas
        queryset = Plant.objects.all()

        # Obtendo filtros com informações da requisição
        filter = self.request.GET.get('filter', '')
        filter_type = self.request.GET.get('filter_type', '')
        search = self.request.GET.get('search', '')

        # Filtrando: (Arrumar)
        queryset = Plant.objects.filter(name__icontains=search)
        if filter_type == 'family':
            queryset = Plant.objects.filter(family=filter)

        elif filter_type == 'division':
            queryset = Plant.objects.filter(division=filter)

        return queryset


    #Para criar barra de pesquisa
    #barra de pesquisa ainda não tão funcional quanto deveria ser
    def get_context_data(self,**kwargs ): # Sobreescrita de método
        context = super().get_context_data(**kwargs)
        #Pegando as escolhas para o filtros
        context['families'] = Plant.FAMILY_CHOICES
        context['form'] = SearchForm(self.request.GET or None)

        return context

class HerbariumDetail(DetailView):
    # Mostra detalhes de uma planta em específico. Passa no contexto os dados de UMA planta
    model = Plant
    template_name = 'herbarium/detail.html'


# ????
index = HerbariumIndex.as_view();
detail = HerbariumDetail.as_view();
