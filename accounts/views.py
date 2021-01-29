from django.shortcuts import render
from .forms import UserForm

# Create your views here.

def create_user(request):
    """Função que cria um novo usuário"""

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        # Cria uma instância com os dados da requisição
        form = UserForm(request.POST)

        if form.is_valid():
            form.save()
            return "Usuário Cadastrado"

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        form = UserForm()

    context = {
        'form': form
    }

    # Renderiza a página de criar turma
    return render(request, 'registration/create.html', context)