from django.http import HttpResponse, JsonResponse

from django.utils.timezone import localtime, make_aware

from alerts.models import MathModel


def get_mathmodels(request):
    mathmodels = MathModel.objects.all()
    mathmodels_response = {}
    for mathmodel in mathmodels:
        mathmodels_response[mathmodel.id] = {}
        data_x = []
        data_y = []
        if mathmodel.mathmodelresult_set.all():
            results = mathmodel.mathmodelresult_set.all().values('date', 'value')
            data_x = [localtime(x['date']) for x in results]
            data_y = [x['value'] for x in results]
            mathmodels_response[mathmodel.id] = {"name": mathmodel.name, "x": data_x, "y": data_y}

    return JsonResponse(mathmodels_response)
