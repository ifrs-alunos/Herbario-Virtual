from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def board_notify(request):
    print(f"Placa {request.POST.get('chip_id')} foi iniciada.")
    return HttpResponse("")
