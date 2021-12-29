from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from accounts.forms import ProfileForm, UserUpdateForm, SolicitationForm, DiseaseCharSolicitationModelForm, CultureSolicitationModelForm
from accounts.models import Profile, Solicitation, PlantSolicitation, PhotoSolicitation, DiseaseSolicitation, \
    CharSolicitationModel, DiseasePhotoSolicitation
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from herbarium.models import Plant
from herbarium.forms import PlantForm, PhotoForm
from disease.models import Disease, Culture, Condition, MathModels
from disease.forms import DiseaseForm, MathModelsForm, DiseasePhotoForm
from .models import Contribuition

from .forms import  UserForm, SolicitationStatusUpdateForm

class ProfileView(TemplateView):
    template_name = "accounts/profile.html"

class InfoView(TemplateView):
    template_name = "accounts/info.html"

def create_user(request):
    """Função que cria um novo usuário"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if form.is_valid() and profile_form.is_valid():
            user = form.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            # Tornando todos usuários comuns
            group = Group.objects.get_or_create(name="common_users")
            user.groups.add(group)

            return redirect('accounts:login')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        form = UserForm()
        profile_form = ProfileForm()

    context = {
        'form': form,
        'profile_form': profile_form,
    }

    # Renderiza a página de criar turma
    return render(request, 'registration/create.html', context)


class DashboardView(TemplateView):
    template_name = "dashboard/dashboard.html"


def update_profile(request):
    """Esta função exibe ou edita um perfil de um usuário, a depender do método da requisição"""

    # Tenta obter o objeto com a pk informado. Se não conseguir, retorna um erro 404
    profile = get_object_or_404(Profile, user=request.user)
    print(request.user, profile)

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Instancia um formulário vinculado a um objeto Turma com os dados recebidos da requisição POST
        form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()

            # Retorna para a página de lista de turmas
            return redirect("accounts:view_dashboard")

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria uma instância com os dados do objeto passado como parâmetro
        form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile_form": profile_form,
        "link": "profile"
    }

    # Renderiza a página de editar turma com os campos e seus respectivos dados
    return render(request, "accounts/profile.html", context)


'''
class CreatePlantView(PermissionRequiredMixin, CreateView):
    permission_required = 'herbarium.add_plant'

class UpdatePlantView(PermissionRequiredMixin, UpdateView):
    permission_required = 'herbarium.change_plant'

class DeletePlantView(PermissionRequiredMixin, DeleteView):
    permission_required = 'herbarium.delete_plant'
'''


class SolicitationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Essa classe cria uma nova solicitação. É acessada somente pelo grupo de "usuários comuns" do sistema"""

    model = Solicitation
    form_class = SolicitationForm
    permission_required = 'accounts.add_solicitation'
    template_name = 'dashboard/solicitation.html'
    success_url = reverse_lazy('accounts:solicitation')

    def get_initial(self):
        initial = super().get_initial()
        initial['user'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # Recupera a última solicitação do usuário logado
        solicitation = self.request.user.solicitations.last()

        # Cria novos contextos
        data['link'] = 'solicitation'
        data['solicitation'] = solicitation

        return data

    def post(self, request, *args, **kwargs):
        # Verifica se o usuário logado tem permissão para enviar uma NOVA solicitação por método POST
        if request.user.profile.can_send_solicitation() == True:
            return super().post(request, *args, **kwargs)
        else:
            return self.handle_no_permission()


class SolicitationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Essa classe lista todas as solicitações. É acessada somente por um administrador do sistema"""

    model = Solicitation
    permission_required = 'auth.view_user'
    template_name = 'dashboard/solicitation_list.html'
    context_object_name = 'solicitations'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'solicitation-list'  # Cria novo contexto

        return data

    def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=Solicitation.Status.SENT)

        return queryset


class SolicitationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Essa classe atualiza o status de uma solicitação. É realizada somente por um administrador do sistema"""

    model = Solicitation
    form_class = SolicitationStatusUpdateForm
    permission_required = 'auth.view_user'
    template_name = 'dashboard/solicitation_update.html'
    success_url = reverse_lazy('accounts:solicitation_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'solicitation-list'  # Cria novo contexto

        return data

    def form_valid(self, form):
        solicitation = form.save()

        if solicitation.status == "accepted":  # Verifica se a solicitação salva foi aceita
            user = solicitation.user  # Recupera o usuário da solicitação

            old_group = Group.objects.get_or_create(name="common_users")
            new_group = Group.objects.get_or_create(name="contributors")

            user.groups.remove(old_group)  # Retira o grupo de usuário comum
            user.groups.add(new_group)  # Adiciona o grupo de contribuidor

        return redirect("accounts:solicitation_list")


class ChangePassword(PasswordChangeView):
    template_name = 'dashboard/change_password.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'change-password'  # Cria novo contexto

        return data

    def get_success_url(self):
        return reverse('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, "Sua senha foi alterada com sucesso!")
        return super().form_valid(form)


class ContributionTemplateView(ListView):
    template_name = 'dashboard/contributions.html'
    model = Contribuition

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['link'] = 'contributions'  # Cria novo contexto

        return data

    def get_queryset(self):
        result = set()
        if self.request.user.is_authenticated:
            profile = self.request.user.profile
            result = Contribuition.objects.all().filter(profile=profile.pk)
        return result


class HerbariumListView(ListView):
    model = Plant
    context_object_name = 'plants'
    template_name = 'dashboard/herbarium_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'herbarium-update'  # Cria novo contexto

        return data


class UserListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'dashboard/user_list.html'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(is_superuser=True)  # Exclui superusers
        queryset = queryset.exclude(groups__name="admins")  # Exclui contas com grupo 'admin-group'

        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'user-list'  # Cria novo contexto

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

            return redirect('accounts:herbarium_update')

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

            return redirect('accounts:view_dashboard')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        photo_form = PhotoForm()

    context = {
        'photo_form': photo_form,
        'link': 'photo-solicitation',
    }

    return render(request, 'dashboard/photo_solicitation.html', context)

def disease_solicitation(request):
    """Essa função cria uma solicitação para cadastrar uma nova doença"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        disease_form = DiseaseForm(request.POST)

        if disease_form.is_valid():
            disease = disease_form.save()  # Cria objeto mas nao salva no banco de dados
            disease.published = False

            disease_solicitation = DiseaseSolicitation(user=request.user, status='sent', new_disease=disease)
            disease_solicitation.save()
            chars = {}

            for label in request.POST.keys():
                if "charval-" in label:
                    chars[label.replace('charval-', '')]['value'] = request.POST[label]
                elif "char-" in label:
                    chars[label.replace('char-', '')] = {'id': int(request.POST[label]), 'value':None}

            for char in chars.keys():
                c = Condition.objects.create(characteristic_id=int(chars[char]['id']), disease=disease)
                c.set_value(chars[char]['value'])

            return redirect('accounts:disease_update')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        disease_form = DiseaseForm()

    context = {
        'disease_form': disease_form,
        'link': 'disease-solicitation',
        'characteristics_inputs': [{'id': x.id, 'type': x.get_html_input()} for x in CharSolicitationModel.objects.all()]
    }

    return render(request, 'dashboard/disease_solicitation.html', context)

def disease_update(request, pk):
    """Essa função cria uma solicitação para cadastrar uma nova doença"""

    disease = get_object_or_404(Disease, id=pk)

    disease_form = DiseaseForm(request.POST or None, instance=disease)
    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição

        if disease_form.is_valid():
            disease = disease_form.save()

            disease.condition_set.all().delete()

            chars = {}

            for label in request.POST.keys():
                if "charval-" in label:
                    chars[label.replace('charval-', '')]['value'] = request.POST[label]
                elif "char-" in label:
                    chars[label.replace('char-', '')] = {'id': int(request.POST[label]), 'value': None}

            for char in chars.keys():
                c = Condition.objects.create(characteristic_id=int(chars[char]['id']), disease=disease)
                c.set_value(chars[char]['value'])

            return redirect('accounts:disease_update')
    print(disease.condition_set.all())

    context = {
        'disease_form': disease_form,
        'link': 'disease_update',
        'conditions': [(x, y) for x, y in enumerate(disease.condition_set.all())],
        'conditions_lenght': len(disease.condition_set.all()),
        'characteristics_inputs': [{'id': x.id, 'type': x.get_html_input()} for x in
                                   CharSolicitationModel.objects.all()]
    }

    return render(request, 'dashboard/disease_solicitation.html', context)

def disease_photo_solicitation(request):
    """Essa função cria uma solicitação para enviar uma imagem de uma doença"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        disease_photo_form = DiseasePhotoForm(request.POST, request.FILES)

        if disease_photo_form.is_valid():
            disease_photo = disease_photo_form.save()  # Cria objeto mas nao salva no banco de dados
            disease_photo.published = False

            disease_photo_solicitation = DiseasePhotoSolicitation(user=request.user, status='sent', new_photo=disease_photo)
            disease_photo_solicitation.save()

            return redirect('accounts:view_dashboard')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        disease_photo_form = DiseasePhotoForm()

    context = {
        'disease_photo_form': disease_photo_form,
        'link': 'disease-photo-solicitation',
    }

    return render(request, 'dashboard/disease_photo_solicitation.html', context)

def disease_char_solicitation(request):
    """Essa função cria uma solicitação para cadastrar uma nova condição para desenvolvimento de doença"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        disease_char_form = DiseaseCharSolicitationModelForm(request.POST)

        if disease_char_form.is_valid():
            disease_char = disease_char_form.save()  # Cria objeto mas nao salva no banco de dados
            return redirect('accounts:char_phytopathological')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        disease_char_form = DiseaseCharSolicitationModelForm()

    context = {
        'disease_char_form': disease_char_form,
        'link': 'disease-char-solicitation',
    }

    return render(request, 'dashboard/disease_condition_solicitation.html', context)

def char_update(request, pk):
    """Essa função cria uma solicitação para cadastrar uma nova doença"""

    char = get_object_or_404(CharSolicitationModel, id=pk)

    char_form = DiseaseCharSolicitationModelForm(request.POST or None, instance=char)
    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição

        if char_form.is_valid():
            char_form.save()

            return redirect('accounts:char_phytopathological')

    context = {
        'disease_char_form': char_form,
        'link': 'char_update',
    }

    return render(request, 'dashboard/disease_condition_solicitation.html', context)

def culture_solicitation(request):
    """Essa função cria uma solicitação para cadastrar uma nova cultura"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        culture_form = CultureSolicitationModelForm(request.POST)

        if culture_form.is_valid():
            culture_form = culture_form.save()  # Cria objeto mas nao salva no banco de dados

            return redirect('accounts:culture_list')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        culture_form = CultureSolicitationModelForm()

    context = {
        'culture_form': culture_form,
        'link': 'culture_solicitation',
    }

    return render(request, 'dashboard/culture_solicitation.html', context)

def culture_update(request, pk):
    """Essa função cria uma solicitação para cadastrar uma nova doença"""

    culture = get_object_or_404(Culture, id=pk)

    culture_form = CultureSolicitationModelForm(request.POST or None, instance=culture)
    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição

        if culture_form.is_valid():
            culture_form.save()

            return redirect('accounts:culture_list')

    context = {
        'culture_form': culture_form,
        'link': 'culture_update',
    }

    return render(request, 'dashboard/culture_solicitation.html', context)

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

            return redirect('accounts:herbarium_update')

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

# Views relacionadas à doenças

class DiseasePhotoSolicitationListView(ListView):
    model = DiseasePhotoSolicitation
    context_object_name = 'solicitations'
    template_name = 'dashboard/disease_photo_solicitation_list.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'disease-photo-solicitation-list'  # Cria novo contexto

        return data

    def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=DiseasePhotoSolicitation.Status.SENT)

        return queryset

class DiseaseListView(ListView):
    model = Disease
    context_object_name = 'diseases'
    template_name = 'dashboard/phytopathological_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'disease_update'  # Cria novo contexto

        return data


class DiseaseSolicitationListView(ListView):
    model = DiseaseSolicitation
    context_object_name = 'solicitations'
    template_name = 'dashboard/disease_solicitation_list.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'disease-solicitation-list'  # Cria novo contexto

        return data

    def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=DiseaseSolicitation.Status.SENT)

        return queryset

class CharListView(ListView):
    model = CharSolicitationModel
    context_object_name = 'characteristics'
    template_name = 'dashboard/phytopathological_char.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'char_phytopathological'  # Cria novo contexto

        return data


class DiseaseSolicitationListView(ListView):
    model = DiseaseSolicitation
    context_object_name = 'solicitations'
    template_name = 'dashboard/disease_solicitation_list.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'disease-solicitation-list'  # Cria novo contexto

        return data

    def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=DiseaseSolicitation.Status.SENT)

        return queryset

class DiseaseDetailView(DetailView):
    # Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
    model = Disease
    template_name = 'dashboard/disease_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context



class DiseaseSolicitationDetailView(DetailView):
    # Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
    model = DiseaseSolicitation
    template_name = 'dashboard/disease_solicitation_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

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

class DiseasePhotoSolicitationDetailView(DetailView):
    # Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
    model = DiseasePhotoSolicitation
    template_name = 'dashboard/disease_photo_solicitation_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

class PlantDeleteView(DeleteView):
    model = Plant
    success_url = reverse_lazy('accounts:herbarium_update')

class PlantSolicitationDeleteView(DeleteView):
    model = PlantSolicitation
    success_url = reverse_lazy('accounts:plant_solicitation_list')

class PlantPhotoSolicitationDeleteView(DeleteView):
    model = PhotoSolicitation
    success_url = reverse_lazy('accounts:photo_solicitation_list')

class DiseaseSolicitationDeleteView(DeleteView):
    model = DiseaseSolicitation
    success_url = reverse_lazy('accounts:disease_solicitation_list')

class DiseasePhotoSolicitationDeleteView(DeleteView):
    model = DiseasePhotoSolicitation
    success_url = reverse_lazy('accounts:disease_photo_solicitation_list')

class DiseaseDeleteView(DeleteView):
    model = Disease
    success_url = reverse_lazy('accounts:disease_update')

class CharDeleteView(DeleteView):
    model = CharSolicitationModel
    success_url = reverse_lazy('accounts:char_phytopathological')

class CultureDeleteView(DeleteView):
    model = Culture
    success_url = reverse_lazy('accounts:culture_list')

class CharDetailView(DetailView):
    # Mostra detalhes de uma característica em específico. Passa no contexto os dados de UMA característica
    model = CharSolicitationModel
    template_name = 'dashboard/char_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

class CultureListView(ListView):
    model = Culture
    context_object_name = 'culture'
    template_name = 'dashboard/culture_list.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'culture_list'  # Cria novo contexto

        return data

def math_model_solicitation(request):
    """Essa função cadastra um novo modelo matemático"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        math_model_form = MathModelsForm(request.POST)

        if math_model_form.is_valid():
            math_model_form = math_model_form.save()  # Cria objeto mas nao salva no banco de dados

            return redirect('accounts:math_model_solicitation')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        math_model_form = MathModelsForm()

    context = {
        'math_model_form': math_model_form,
        'link': 'math_model_solicitation',
    }

    return render(request, 'dashboard/math_model_add.html', context)

class MathModelsListView(ListView):
    model = MathModels
    context_object_name = 'math_model'
    template_name = 'dashboard/math_model_list.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'math_models'  # Cria novo contexto

        return data

@login_required
def accept_plant_solicitation(request, pk):

    if request.method == "GET" and request.user.has_perm('change_plant'):
        plant = PlantSolicitation.objects.filter(id=pk).first()
        plant.status = "accepted"
        plant.save()

        np = plant.new_plant

        np.published = True
        np.save()

    return redirect("accounts:plant_solicitation_list")


def accept_disease_solicitation(request, pk):
    if request.method == "GET" and request.user.has_perm('change_disease'):
        disease = DiseaseSolicitation.objects.filter(id=pk).first()
        disease.status = "accepted"
        disease.save()

        nd = disease.new_disease

        nd.published_disease = True
        nd.save()

    return redirect("accounts:disease_solicitation_list")

def accept_plant_photo_solicitation(request, pk):
    if request.method == "GET" and request.user.has_perm('change_plant'):
        plant_photo = DiseaseSolicitation.objects.filter(id=pk).first()
        plant_photo.status = "accepted"
        plant_photo.save()

        np = plant_photo.plant

        np.published = True
        np.save()

    return redirect("accounts:photo_solicitation_list")

def accept_disease_photo_solicitation(request, pk):
    if request.method == "GET" and request.user.has_perm('change_disease'):
        photo_disease = DiseaseSolicitation.objects.filter(id=pk).first()
        photo_disease.status = "accepted"
        photo_disease.save()

        np = photo_disease.disease

        np.published = True
        np.save()

    return redirect("accounts:disease_photo_solicitation_list")