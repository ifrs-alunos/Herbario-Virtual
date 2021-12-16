from django.db.models import Q
from django.shortcuts import render
from ..models import Station
from django.views.generic import ListView, DetailView


class StationIndex(ListView):
    model = Station
    template_name = 'index.html'
    context_object_name = 'stations'

    paginate_by = 12

    def get_queryset(self, **kwargs):
        # Seleciona todas as estações

        stations = Station.objects.all()

        return stations


class StationDetail(DetailView):
    # Mostra detalhes de uma estação específica. Passa no contexto os dados de uma estação
    model = Station
    template_name = 'detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        print(context)

        return context
