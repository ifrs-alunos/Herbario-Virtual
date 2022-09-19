import asyncio
from django.http import HttpResponse


async def collect_data_cepadi(request):
    loop = asyncio.get_event_loop()
    return HttpResponse("Dados cepadi")
