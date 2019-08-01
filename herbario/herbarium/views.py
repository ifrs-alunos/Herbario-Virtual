from django.shortcuts import render
from django.views.generic import ListView,  DetailView

from .models import Plant
from .forms import SearchForm

# Create your views here.


class HerbariumIndex(ListView):
    model = Plant
    template_name = 'herbarium/index.html'

    #Pegando Queryset
    def get_queryset(self):
        queryset = Plant.objects.all()

        filter = self.request.GET.get('filter', '')
        filter_type = self.request.GET.get('filter_type', '')
        search = self.request.GET.get('search', '')

        queryset = Plant.objects.filter(name__icontains=search)
        if filter_type == 'class':
            
            queryset = Plant.objects.filter(plant_class=filter)

        return queryset


    #Para criar barra de pesquisa
    #barra de pesquisa ainda não tão funcional quanto deveria ser
    def get_context_data(self,**kwargs ):
        context = super().get_context_data(**kwargs)
        #Pegando as escolhas para o filtros
        context['classes'] = Plant.PLANT_CLASS_CHOICES
        context['form'] = SearchForm(self.request.GET or None)

        return context


class HerbariumDetail(DetailView):
    model = Plant
    template_name = 'herbarium/detail.html'



index = HerbariumIndex.as_view();
detail = HerbariumDetail.as_view();
