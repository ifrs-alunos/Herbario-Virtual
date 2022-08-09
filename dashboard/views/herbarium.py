from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse_lazy

from django.views.generic import ListView, DetailView, DeleteView

from ..models import PlantSolicitation, PhotoSolicitation
from herbarium.models import Plant
from herbarium.forms import PlantForm, PhotoForm


class HerbariumListView(ListView):
    model = Plant
    context_object_name = 'plants'
    template_name = 'dashboard/herbarium_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'herbarium-update'  # Cria novo contexto

        return data


def plant_solicitation(request):
    """Essa função cria uma solicitação para enviar uma nova planta"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        plant_form = PlantForm(request.POST)

        if plant_form.is_valid():
            plant = plant_form.save()  # Cria objeto mas nao salva no banco de dados
            plant.published = False

            plant_solicitation = PlantSolicitation(user=request.user, status='sent', new_plant=plant)
            plant_solicitation.save()

            return redirect('dashboard:herbarium_update')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        plant_form = PlantForm()

    context = {
        'plant_form': plant_form,
        'link': 'plant-solicitation',
    }

    return render(request, 'dashboard/plant_solicitation.html', context)


def photo_solicitation(request):
    """Essa função cria uma solicitação para enviar uma nova planta"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        photo_form = PhotoForm(request.POST, request.FILES)

        if photo_form.is_valid():
            photo = photo_form.save()  # Cria objeto mas nao salva no banco de dados
            photo.published = False

            photo_solicitation = PhotoSolicitation(user=request.user, status='sent', new_photo=photo)
            photo_solicitation.save()

            return redirect('dashboard:view_dashboard')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        photo_form = PhotoForm()

    context = {
        'photo_form': photo_form,
        'link': 'photo-solicitation',
    }

    return render(request, 'dashboard/photo_solicitation.html', context)


class PlantSolicitationListView(ListView):
    model = PlantSolicitation
    context_object_name = 'solicitations'
    template_name = 'dashboard/plant_solicitation_list.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'plant-soliciation-list'  # Cria novo contexto

        return data

    def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=PlantSolicitation.Status.SENT)

        return queryset


def plant_update(request, pk):
    """Essa função edita uma doença"""

    plant = get_object_or_404(Plant, id=pk)

    plant_form = PlantForm(request.POST or None, instance=plant)
    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição

        if plant_form.is_valid():
            plant_form.save()

            return redirect('dashboard:herbarium_update')

    context = {
        'plant_form': plant_form,
        'link': 'plant_update',
    }

    return render(request, 'dashboard/plant_solicitation.html', context)


class PlantDetailView(DetailView):
    # Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
    model = Plant
    template_name = 'dashboard/plant_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class PhotoSolicitationListView(ListView):
    model = PhotoSolicitation
    context_object_name = 'solicitations'
    template_name = 'dashboard/photo_solicitation_list.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'photo-solicitation-list'  # Cria novo contexto

        return data

    def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=PhotoSolicitation.Status.SENT)

        return queryset


class PlantSolicitationDetailView(DetailView):
    # Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
    model = PlantSolicitation
    template_name = 'dashboard/plant_solicitation_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class PlantPhotoSolicitationDetailView(DetailView):
    # Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
    model = PhotoSolicitation
    template_name = 'dashboard/plant_photo_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class PlantDeleteView(DeleteView):
    model = Plant
    success_url = reverse_lazy('dashboard:herbarium_update')


class PlantSolicitationDeleteView(DeleteView):
    model = PlantSolicitation
    success_url = reverse_lazy('dashboard:plant_solicitation_list')


class PlantPhotoSolicitationDeleteView(DeleteView):
    model = PhotoSolicitation
    success_url = reverse_lazy('dashboard:photo_solicitation_list')


@login_required
def accept_plant_solicitation(request, pk):
    if request.method == "GET" and request.user.has_perm('herbarium.change_plant'):
        plant = PlantSolicitation.objects.filter(id=pk).first()
        plant.status = "accepted"
        plant.save()

        np = plant.new_plant

        np.published = True
        np.save()

    return redirect("dashboard:plant_solicitation_list")


def accept_plant_photo_solicitation(request, pk):
    if request.method == "GET" and request.user.has_perm('herbarium.change_plant'):
        plant_photo = PhotoSolicitation.objects.filter(id=pk).first()
        plant_photo.status = "accepted"
        plant_photo.save()

        np = plant_photo.new_photo

        np.published = True
        np.save()

    return redirect("dashboard:photo_solicitation_list")
