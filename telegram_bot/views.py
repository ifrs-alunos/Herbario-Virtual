from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from telegram import Update
from asgiref.sync import async_to_sync

from .handlers import TelegramBot

@csrf_exempt
@require_POST
def telegram_webhook(request):
    """View para webhook do Telegram"""
    try:
        bot = TelegramBot()
        if not bot.application:
            return JsonResponse({"status": "error", "message": "Bot not initialized"}, status=500)
        
        # Processa o update
        update = Update.de_json(json.loads(request.body), bot.application.bot)
        async_to_sync(bot.application.process_update)(update)
        
        return JsonResponse({"status": "ok"})
        
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)