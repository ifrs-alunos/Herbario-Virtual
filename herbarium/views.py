from django.shortcuts import render
from django.views.generic import ListView,  DetailView, TemplateView

from .models import Plant, Family
from .forms import SearchForm

# Create your views here.


# Lista as plantas cadastradas
class HerbariumIndex(ListView):
    model = Plant
    template_name = 'herbarium/index.html'
    context_object_name = 'plants'

    paginate_by = 10

    # Funcionalidade adicional: lista famílias de plantas ao sobreescrever método get_context_data
    def get_context_data(self, **kwargs):
        # Pega contextos prévios da superclasse (ListView)
        context = super().get_context_data(**kwargs)

        # Adiciona um contexto novo, o qual pega todos os objetos do tipo Family
        context["families"] = Family.objects.all()
        context["selected_family"] = self.kwargs.get("family")
        # context["families1"] = Family.objects.filter(division__name="Monocotiledôneas")
        # context["families2"] = Family.objects.filter(division__name="Dicotiledôneas")

        # Retorna o contexto
        return context

    def get_queryset(self, **kwargs):
        print(self.kwargs)

        # Se o dicionário da requisição não for vazio, ou seja, não contiver nenhuma família especificada
        if self.kwargs != {}:
            # Seleciona todas as plantas de uma família que se encontra na chave do dicionário da requisição
            plants_by_family = Plant.objects.filter(family__name=self.kwargs['family'])

            # Retorna a lista de plantas
            return plants_by_family

        # Se estiver vazio, ou seja, se acessar a página inicial do herbário e não selecionar nenhum filtro por família
        else:
            # Seleciona todas as plantas cadastradas
            all_plants = Plant.objects.all()

            # Retorna a lista de todas as plantas
            return all_plants

    '''
    # Não necessário agora

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

    '''


class HerbariumDetail(DetailView):
    # Mostra detalhes de uma planta em específico. Passa no contexto os dados de UMA planta
    model = Plant
    template_name = 'herbarium/detail.html'


# index = HerbariumIndex.as_view();
# detail = HerbariumDetail.as_view();
