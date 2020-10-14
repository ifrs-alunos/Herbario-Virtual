from django.shortcuts import render
from .models import Highlight

# Create your views here.

def index(request):
    template_name = 'core/index.html'
    highlights = Highlight.objects.all()
    # print(highlights)

    # for i in highlights:
    # 	print(i.text)

    return render(request, template_name, {'destaques':highlights})

def subjects(request):
    template_name = 'core/subjects.html'

    return render(request, template_name, {})
