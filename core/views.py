from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from .models import Highlight, CarouselImage, Colaborators
from .forms import ColaboratorsModelForm


# Create your views here.

def index(request):
    template_name = 'core/index.html'

    # Seleciona todos os objetos do tipo Highlight
    highlights = Highlight.objects.all()

    # Seleciona todos os objetos do tipo CarouselImage
    carousel_images = CarouselImage.objects.all()

    return render(request, template_name, {'destaques': highlights, 'imagens_carrossel': carousel_images})


def subjects(request):
    template_name = 'core/subjects.html'

    return render(request, template_name, {})

def colaborators_edit(request):
    """Essa função cria uma solicitação para enviar uma nova planta"""

    colaborators_form = ColaboratorsModelForm(request.POST or None, instance=Colaborators)

    # Se o usuário mandar dados, ou seja, se a requisição for POST
    if request.method == "POST":
        colaborators_form = ColaboratorsModelForm(request.POST)

        if colaborators_form.is_valid():
            colaborators_form = colaborators_form.save()  # Cria objeto mas nao salva no banco de dados

            return redirect('core:about')

    # Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
    else:
        # Cria um formulário em branco
        colaborators_form = ColaboratorsModelForm()

    context = {
        'colaborators_form': colaborators_form,
        'link': 'edit-about',
    }

    return render(request, 'core/edit-about.html', context)

class ColaboratorsListView(ListView):
    model = Colaborators
    context_object_name = 'colaborators'
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'about'  # Cria novo contexto

        return data

def highlight(request, highlight_slug):
    template_name = 'core/highlights.html'

    highlight = Highlight.objects.get(slug=highlight_slug)

    return render(request, template_name, {'highlight': highlight})
