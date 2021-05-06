from django.shortcuts import render, get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.detail import DetailView
from accounts.forms import ProfileForm, UserUpdateForm, UserUpdateForm, SolicitationForm
from accounts.models import Profile, Solicitation
from dashboard.forms import SolicitationStatusUpdateForm
    
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

        # Cria novo contexto
        data['link'] =  'solicitation-list'

        return data

class SolicitationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Essa classe atualiza o status de uma solicitação. É realizada somente por um administrador do sistema"""

    model = Solicitation
    form_class = SolicitationStatusUpdateForm
    permission_required =  'auth.view_user'
    template_name = 'dashboard/solicitation_update.html'
    success_url = reverse_lazy('dashboard:solicitation_list')

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)

        # Cria novo contexto
        data['link'] =  'solicitation-list'

        return data