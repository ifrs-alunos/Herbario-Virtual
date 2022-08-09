from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# from .utils import create_report_from_params
#
#
# # views
#
# @csrf_exempt
# def save_report(request):
#     params = request.POST
#
#     report = create_report_from_params(params)
#
#     return HttpResponse(":)")
