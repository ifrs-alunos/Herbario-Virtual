
# from alerts.models import Formula, ReportOld

#
# def create_formula(request):
#     if request.method == 'POST':
#         form = FormulaForm(request.POST)
#         if form.is_valid():
#             cleaned_data = form.cleaned_data
#
#             constants = None
#             if cleaned_data.get('constants'):
#                 request_constants = cleaned_data.get('constants').split('\r\n')
#                 constants = dict([(k, v) for k, v in [x.split('=') for x in request_constants]])
#
#             Formula.objects.create(
#                 **{'name': cleaned_data.get('name'),
#                    'constants': constants,
#                    'expression': cleaned_data.get('expression')}
#             ).save()
#
#             return redirect('alerts:alerts')
#
#     else:
#         form = FormulaForm()
#
#     context = {'form': form,
#                'report_fields': ReportOld.objects.last().get_fields(
#                    ["id", "station", "station_identificator", "board_time"])}
#
#     return render(request, 'create_formula.html', context)
