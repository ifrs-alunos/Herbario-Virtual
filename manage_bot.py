#!/usr/bin/env python
import os
import django
import logging
import time

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        print("🚀 Iniciando Bot do Telegram...")
        
        from telegram_bot.handlers import TelegramBot
        bot = TelegramBot()
        
        print("✅ Bot inicializado!")
        print("📱 Envie /start para seu bot no Telegram")
        print("⏹️  Pressione Ctrl+C para parar\n")
        
        # Mantém o script rodando
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Encerrando bot...")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()