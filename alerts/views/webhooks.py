import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def whatsapp(request):
    if request.method == "POST":
        # Message is a json object with the following structure:
        # https://docs.wwebjs.dev/Message.html
        data = json.loads(request.body)

        print(data)

        body: str | None = data.get("body")
        if isinstance(body, str) and (len(body) == 6 and body.isnumeric()):
            ...

    return JsonResponse({"message": "ok"})
