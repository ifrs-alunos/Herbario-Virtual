from django.contrib import admin
from .models.message import Message
from .models.message_confirmation import MessageConfirmation
# Register your models here.

admin.site.register(Message)

@admin.register(MessageConfirmation)
class MessageConfirmationAdmin(admin.ModelAdmin):
    ...