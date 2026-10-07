from django.apps import AppConfig

class TelegramBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram_bot'
    verbose_name = 'Bot do Telegram'
    
    def ready(self):
        # Registra o receiver que mantém o vínculo em dia quando o perfil muda
        import telegram_bot.signals  # noqa: F401
