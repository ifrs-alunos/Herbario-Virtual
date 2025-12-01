from django.db.models import FloatField, Avg
from django.db.models.functions import Cast, TruncMonth, TruncDay
from django.http import JsonResponse
from django.utils import timezone

from django.utils.timezone import localtime

from alerts.models import MathModel


def get_mathmodels(request, date_filter):
    date = date_filter
    mathmodels = MathModel.objects.all()
    mathmodels_response = {}
    for mathmodel in mathmodels:
        mathmodels_response[mathmodel.id] = {}
        data_x = []
        data_y = []
        if mathmodel.mathmodelresult_set.all():
            last_mathmodel_result_date = localtime(mathmodel.mathmodelresult_set.all().last().date)

            if date == "day":
                results = (
                    mathmodel.mathmodelresult_set.all()
                    .filter(
                        date__day=last_mathmodel_result_date.day,
                        date__year=last_mathmodel_result_date.year,
                        date__month=last_mathmodel_result_date.month,
                    )
                    .values("date", "value")
                )
                data_x = [localtime(x["date"]) for x in results]
                data_y = [x["value"] for x in results]

            elif date == "week":
                end_week = last_mathmodel_result_date
                start_week = end_week - timezone.timedelta(7)
                results = (
                    mathmodel.mathmodelresult_set.all()
                    .filter(date__range=[start_week, end_week])
                    .values("date", "value")
                    .annotate(value_float=Cast("value", output_field=FloatField()))
                    .annotate(day=TruncDay("date"))
                    .values("day")
                    .annotate(avg_value=Avg("value_float"))
                    .order_by("day")
                )
                data_x = [localtime(x["day"]) for x in results]
                data_y = [x["avg_value"] for x in results]

            elif date == "month":
                results = (
                    mathmodel.mathmodelresult_set.all()
                    .filter(date__year=last_mathmodel_result_date.year)
                    .filter(date__month=last_mathmodel_result_date.month)
                    .annotate(value_float=Cast("value", output_field=FloatField()))
                    .annotate(day=TruncDay("date"))
                    .values("day")
                    .annotate(avg_value=Avg("value_float"))
                    .order_by("day")
                )
                data_x = [localtime(x["day"]) for x in results]
                data_y = [x["avg_value"] for x in results]

            elif date == "year":
                results = (
                    mathmodel.mathmodelresult_set.all()
                    .filter(date__year=last_mathmodel_result_date.year)
                    .annotate(value_float=Cast("value", output_field=FloatField()))
                    .annotate(month=TruncMonth("date"))
                    .values("month")
                    .annotate(avg_value=Avg("value_float"))
                    .order_by("month")
                )
                data_x = [localtime(x["month"]) for x in results]
                data_y = [x["avg_value"] for x in results]

            elif date == "all":
                results = mathmodel.mathmodelresult_set.all().values("date", "value")

                data_x = [localtime(x["date"]) for x in results]
                data_y = [x["value"] for x in results]
            else:
                data_x = []
                data_y = []
                
            mathmodels_response[mathmodel.id] = {
                "name": mathmodel.name,
                "x": data_x,
                "y": data_y,
            }

    return JsonResponse(mathmodels_response)
