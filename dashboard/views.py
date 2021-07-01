from django.shortcuts import render, get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from accounts.forms import ProfileForm, UserUpdateForm, UserUpdateForm, SolicitationForm
from accounts.models import Profile, Solicitation, PlantSolicitation, PhotoSolicitation
from dashboard.forms import SolicitationStatusUpdateForm, PlantSolicitationModelForm, PhotoSolicitationModelForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from herbarium.models import Plant
from herbarium.forms import PlantForm, PhotoForm
    
class DashboardView(TemplateView):
    template_name = "dashboard/dashboard.html"

def update_profile(request):
    """Esta função exibe ou edita um perfil de um usuário, a depender do método da requisição"""

    # Tenta obter o objeto com a pk informado. Se não conseguir, retorna um erro 404
    profile = get_object_or_404(Profile, user=request.user)

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Instancia um formulário vinculado a um objeto Turma com os dados recebidos da requisição POST
        form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()

            # Retorna para a página de lista de turmas
            return redirect("dashboard:view_dashboard")
    
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
    return render(request, "dashboard/profile.html", context)

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
    success_url = reverse_lazy('dashboard:solicitation')

    def get_initial(self):
        initial = super().get_initial()
        initial['user'] = self.request.user
        return initial 

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        # Recupera a última solicitação do usuário logado
        solicitation = self.request.user.solicitations.last()

        # Cria novos contextos
        data['link'] =  'solicitation'
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

    model =  Solicitation
    permission_required = 'auth.view_user'
    template_name = 'dashboard/solicitation_list.html' 
    context_object_name = 'solicitations'

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        data['link'] =  'solicitation-list' # Cria novo contexto

        return data

    def get_queryset(self): # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=Solicitation.Status.SENT)
        
        return queryset

class SolicitationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Essa classe atualiza o status de uma solicitação. É realizada somente por um administrador do sistema"""

    model = Solicitation
    form_class = SolicitationStatusUpdateForm
    permission_required =  'auth.view_user'
    template_name = 'dashboard/solicitation_update.html'
    success_url = reverse_lazy('dashboard:solicitation_list')

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        data['link'] =  'solicitation-list' # Cria novo contexto

        return data

    def form_valid(self, form):
        solicitation = form.save()

        if solicitation.status == "accepted": # Verifica se a solicitação salva foi aceita
            user = solicitation.user # Recupera o usuário da solicitação

            old_group = Group.objects.get(name="common_users") 
            new_group = Group.objects.get(name="contributors")

            user.groups.remove(old_group) # Retira o grupo de usuário comum
            user.groups.add(new_group) # Adiciona o grupo de contribuidor

        return redirect("dashboard:solicitation_list")

class ChangePassword(PasswordChangeView):
    template_name = 'dashboard/change_password.html'

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        data['link'] =  'change-password' # Cria novo contexto

        return data
    
    def get_success_url(self):
        return reverse('dashboard:profile')
    
    def form_valid(self, form):
        messages.success(self.request, "Sua senha foi alterada com sucesso!")
        return super().form_valid(form)

class ContributionTemplateView(TemplateView):
    template_name = 'dashboard/contributions.html'

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        data['link'] =  'contributions' # Cria novo contexto

        return data

class HerbariumListView(ListView):
    model = Plant
    context_object_name = 'plants'
    template_name = 'dashboard/herbarium_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        data['link'] =  'herbarium-update' # Cria novo contexto

        return data

class UserListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'dashboard/user_list.html'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(is_superuser=True) # Exclui superusers
        queryset = queryset.exclude(groups__name="admins") # Exclui contas com grupo 'admin-group'
    
        return queryset

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        data['link'] =  'user-list' # Cria novo contexto

        return data

def plant_solicitation(request):
    """Essa função cria uma solicitação para enviar uma nova planta"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        plant_form = PlantForm(request.POST)

        if plant_form.is_valid():
            plant = plant_form.save() # Cria objeto mas nao salva no banco de dados
            plant.published = False

            plant_solicitation = PlantSolicitation(user=request.user, status='sent', new_plant=plant)
            plant_solicitation.save()

            return redirect('dashboard:contributions')

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
            photo = photo_form.save() # Cria objeto mas nao salva no banco de dados
            photo.published = False

            photo_solicitation = PhotoSolicitation(user=request.user, status='sent', new_photo=photo)
            photo_solicitation.save()

            return redirect('dashboard:contributions')

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
        data =  super().get_context_data(**kwargs)

        data['link'] =  'plant-solicitation-list' # Cria novo contexto

        return data

    def get_queryset(self): # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=PlantSolicitation.Status.SENT)
        
        return queryset

class PhotoSolicitationListView(ListView):
    model = PhotoSolicitation
    context_object_name = 'solicitations'
    template_name = 'dashboard/photo_solicitation_list.html'
    
    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        data['link'] =  'photo-solicitation-list' # Cria novo contexto

        return data

    def get_queryset(self): # Filtra as solicitações que estão com o status "enviada"
        queryset = super().get_queryset()
        queryset = queryset.filter(status=PhotoSolicitation.Status.SENT)
        
        return queryset