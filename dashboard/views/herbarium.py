from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
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


@login_required
@permission_required('herbarium.add_plant', raise_exception=True)
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


# raise_exception=True em vez do redirecionamento padrão para o login: quem chega
# aqui já está autenticado e apenas não é contribuidor. Mandá-lo ao login seria um
# laço sem fim.
@login_required
@permission_required('herbarium.add_photo', raise_exception=True)
def photo_solicitation(request):
    """Essa função cria uma solicitação para enviar uma nova foto de planta"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        photo_form = PhotoForm(request.POST, request.FILES)

        if photo_form.is_valid():
            # commit=False é essencial: com photo_form.save() a linha já ia para o
            # banco e o published=False seguinte só existia em memória — a foto
            # nascia com NULL e escapava da fila de revisão.
            photo = photo_form.save(commit=False)
            photo.published = False
            photo.save()  # Photo.save() gera a small_image

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


# As views abaixo — revisão de solicitações de planta, edição e exclusão — não
# tinham verificação nenhuma até 24/09/2026: um visitante anônimo editava e apagava
# plantas (com as fotos, em cascata). A permissão de revisar segue a que
# accept_plant_solicitation já exigia, herbarium.change_plant; apagar a planta exige
# herbarium.delete_plant. As duas pertencem só ao grupo `admins`.
class PlantSolicitationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'herbarium.change_plant'
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


@login_required
@permission_required('herbarium.change_plant', raise_exception=True)
def plant_update(request, pk):
    """Essa função edita uma planta"""

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


class PhotoSolicitationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'herbarium.approve_photo'
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


class PlantSolicitationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    # Tela de revisão: mostra a planta pendente para quem vai decidir sobre ela
    permission_required = 'herbarium.change_plant'
    model = PlantSolicitation
    template_name = 'dashboard/plant_solicitation_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class PlantPhotoSolicitationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    # Tela de revisão: mostra a foto pendente para quem vai decidir sobre ela
    permission_required = 'herbarium.approve_photo'
    model = PhotoSolicitation
    template_name = 'dashboard/plant_photo_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class PlantDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'herbarium.delete_plant'
    model = Plant
    success_url = reverse_lazy('dashboard:herbarium_update')


class PlantSolicitationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    # Apagar a solicitação é recusá-la: mesma permissão de quem aprova
    permission_required = 'herbarium.change_plant'
    model = PlantSolicitation
    success_url = reverse_lazy('dashboard:plant_solicitation_list')


class PlantPhotoSolicitationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'herbarium.approve_photo'
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


# NOTA (02/09/2026): aprovar é um GET, e um GET não deveria mudar estado. Na
# prática isso significa que qualquer coisa que apenas *visite* a URL — o
# pré-carregamento de link do navegador, um antivírus que abre links de e-mail,
# uma <img src> hospedada em outro site — pode publicar a foto sem que o revisor
# tenha clicado. Mantido como está por decisão de escopo; a correção é trocar por
# POST e virar os links de `photo_solicitation_list.html` em
# <form method="post">, como os botões de apagar já são. Vale para todas as
# funções accept_* deste projeto.
@login_required
@permission_required('herbarium.approve_photo', raise_exception=True)
def accept_plant_photo_solicitation(request, pk):
    # A permissão saiu de change_plant para approve_photo: editar o cadastro de uma
    # planta e aprovar a foto de um contribuidor são decisões diferentes. O decorador
    # também troca o antigo "não faz nada e redireciona" por um 403 honesto.
    if request.method == "GET":
        plant_photo = PhotoSolicitation.objects.filter(id=pk).first()
        plant_photo.status = "accepted"
        plant_photo.save()

        np = plant_photo.new_photo

        np.published = True
        np.save()

    return redirect("dashboard:photo_solicitation_list")
