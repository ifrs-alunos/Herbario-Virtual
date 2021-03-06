from .models import Solicitation
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from .forms import ProfileForm, UserForm, SolicitationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from django.contrib.auth.models import Group

# from .forms import UserForm

# Create your views here.

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
            group = Group.objects.get(name="common_users")
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
