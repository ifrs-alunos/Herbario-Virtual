import datetime

from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import date
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from accounts.forms import ProfileForm, UserUpdateForm, SolicitationForm
from accounts.models import Profile, Solicitation
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from ..forms.term_form import TermForm
from accounts.models import Contribuition
from ..forms import UserForm, SolicitationStatusUpdateForm


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
            group, _ = Group.objects.get_or_create(name="common_users")
            user.groups.add(group)

            return redirect('dashboard:login')

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
            return redirect("dashboard:view_dashboard")

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria uma instância com os dados do objeto passado como parâmetro
        form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile_form": profile_form,
        "link": "profile",
        "profile": profile
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
    success_url = reverse_lazy('dashboard:solicitation')

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
        # Gambiarra pro tempo que por algum motivo n tem jeito de colocar dia 'de' mes 'de' 2020
        date_gambi = datetime.datetime.now()
        d = date(date_gambi, 'd')
        m = date(date_gambi, 'F')
        y = date(date_gambi, 'Y')
        data['term_date'] = f'{d} de {m} de {y}'

        data['term_form'] = TermForm()

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
    success_url = reverse_lazy('dashboard:solicitation_list')

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

            user.groups.remove(old_group[0])  # Retira o grupo de usuário comum
            user.groups.add(new_group[0])  # Adiciona o grupo de contribuidor

        return redirect("dashboard:solicitation_list")


class ChangePassword(PasswordChangeView):
    template_name = 'dashboard/change_password.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'change-password'  # Cria novo contexto

        return data

    def get_success_url(self):
        return reverse('dashboard:profile')

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


class UserDetailView(DetailView):
    # Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
    model = Profile
    template_name = 'dashboard/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class ProfileDeleteView(DeleteView):
    model = Profile
    success_url = reverse_lazy('dashboard:user_list')


class SolicitationDeleteView(DeleteView):
    model = Solicitation
    success_url = reverse_lazy('dashboard:solicitation_list')


def accept_solicitation(request, pk):
    if request.method == "GET" and request.user.has_perm('accounts.change_solicitation'):
        solicitation = Solicitation.objects.filter(id=pk).first()
        solicitation.status = "accepted"
        solicitation.save()

    return redirect("dashboard:solicitation_list")


def term_check_password(request):
    """Essa função verifica se a senha dada no request é a mesma do usuario do request"""

    password = request.POST['password']
    user = User.objects.get(id=request.POST['user'])
    match = True if check_password(password, user.password) else False
    return JsonResponse(match, safe=False)
