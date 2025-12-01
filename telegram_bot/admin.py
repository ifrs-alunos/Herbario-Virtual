from django.contrib import admin
from .models import TelegramUser

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'username', 'first_name', 'is_active', 'subscribed_at', 'last_alert_sent')
    search_fields = ('chat_id', 'username', 'first_name')
    list_filter = ('is_active', 'subscribed_at')
    readonly_fields = ('subscribed_at',)