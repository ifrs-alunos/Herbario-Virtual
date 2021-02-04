from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login

# from .forms import UserForm

# Create your views here.

class ProfileView(TemplateView):
    template_name = "registration/profile.html"


def create_user(request):
    """Função que cria um novo usuário"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        form = UserCreationForm(request.POST)
        print(form)

        if form.is_valid():
            form.save()

            return redirect('accounts:login')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        form = UserCreationForm()

    context = {
        'form': form
    }

    # Renderiza a página de criar turma
    return render(request, 'registration/create.html', context)