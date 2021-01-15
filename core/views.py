from django.shortcuts import render
from .models import Highlight, CarouselImage

# Create your views here.

def index(request):
    template_name = 'core/index.html'

    # Seleciona todos os objetos do tipo Highlight
    highlights = Highlight.objects.all()

    # Seleciona todos os objetos do tipo CarouselImage
    carousel_images = CarouselImage.objects.all()

    return render(request, template_name, {'destaques':highlights, 'imagens_carrossel': carousel_images})

def subjects(request):
    template_name = 'core/subjects.html'

    return render(request, template_name, {})

def highlight(request, highlight_slug):
    template_name = 'core/highlights.html'

    highlight = Highlight.objects.get(slug=highlight_slug)

    return render(request, template_name, {'highlight':highlight})
