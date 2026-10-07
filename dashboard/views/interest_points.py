"""Pontos de interesse do usuário para o recebimento de alertas (Alertas → Pontos
de Interesse). Cada usuário só vê e altera os próprios pontos, por isso as views
exigem só login — o filtro por dono está em `InterestPointOwnerMixin`.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.models import Profile
from alerts.geo import geocode
from alerts.models import InterestPoint, Station
from dashboard.forms.interest_point_form import InterestPointForm

__all__ = [
    'InterestPointListView',
    'InterestPointCreateView',
    'InterestPointUpdateView',
    'InterestPointDeleteView',
    'interest_point_geocode',
]


def stations_for_map():
    """Estações com coordenadas, no formato que o mapa do formulário usa"""
    return [
        {'id': s.pk, 'name': s.alias or s.station_id, 'lat': s.lat_coordinate, 'lon': s.lon_coordinate}
        for s in Station.objects.filter(lat_coordinate__isnull=False, lon_coordinate__isnull=False)
    ]


class InterestPointOwnerMixin(LoginRequiredMixin):
    model = InterestPoint
    success_url = reverse_lazy('dashboard:interest_point_list')

    def get_profile(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_queryset(self):
        return InterestPoint.objects.filter(profile__user=self.request.user).select_related('station')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'interest_point_list'
        return context


class InterestPointListView(InterestPointOwnerMixin, ListView):
    template_name = 'dashboard/interest_point_list.html'
    context_object_name = 'interest_points'


class InterestPointFormMixin(InterestPointOwnerMixin):
    form_class = InterestPointForm
    template_name = 'dashboard/interest_point_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stations_json'] = stations_for_map()
        return context


class InterestPointCreateView(InterestPointFormMixin, CreateView):
    def form_valid(self, form):
        form.instance.profile = self.get_profile()
        messages.success(self.request, 'Ponto de interesse cadastrado.')
        return super().form_valid(form)


class InterestPointUpdateView(InterestPointFormMixin, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, 'Ponto de interesse atualizado.')
        return super().form_valid(form)


class InterestPointDeleteView(InterestPointOwnerMixin, DeleteView):
    http_method_names = ['post']

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Ponto de interesse excluído.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_GET
def interest_point_geocode(request):
    """Botão "Localizar" do formulário: devolve as coordenadas de um endereço.

    Passa pelo servidor, e não direto do navegador ao Nominatim, para que a
    política de uso dele (User-Agent, limite de requisições) fique num lugar só.
    """
    result = geocode(request.GET.get('q', ''))
    if result is None:
        return JsonResponse({'found': False}, status=404)

    return JsonResponse({
        'found': True,
        'lat': result.latitude,
        'lon': result.longitude,
        'display_name': result.display_name,
    })
