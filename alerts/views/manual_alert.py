from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from alerts.models import MathModel, Station, AlertHistory
from django.utils import timezone
import requests
from config.settings import TELEGRAM_BOT_TOKEN
from telegram_bot.models import TelegramUser

@login_required
def send_manual_alert(request):
    if request.method == 'POST':
        try:
            math_model_id = request.POST.get('math_model')
            station_id = request.POST.get('station')
            value = float(request.POST.get('value', 0.15))
            custom_message = request.POST.get('message')
            update_math_model = request.POST.get('update_math_model') == 'on'
            temperature = float(request.POST.get('temperature', 25.0))
            humidity = float(request.POST.get('humidity', 80.0))
            
            print(f"DEBUG: Iniciando alerta manual")
            
            if not math_model_id or not station_id or not custom_message:
                messages.error(request, "Preencha todos os campos obrigatórios.")
                return redirect('dashboard:send_manual_alert')
            
            math_model = MathModel.objects.get(id=math_model_id)
            station = Station.objects.get(id=station_id)
            
            if update_math_model:
                math_model.alert_message = custom_message
                math_model.save()
                messages.info(request, f"Mensagem padrão do modelo {math_model.name} atualizada.")
            
            disease_name = math_model.disease.name_disease if math_model.disease else "Doença"
            
            format_data = {
                'value': value,
                'station': station.alias,
                'disease': disease_name,
                'temp': temperature,
                't': temperature,
                'humidity': humidity,
                'rh': humidity,
                'rain': 0,
                'model': math_model.name
            }
            
            try:
                formatted_message = custom_message.format(**format_data)
                print(f"DEBUG: Mensagem formatada com sucesso")
            except KeyError as e:
                formatted_message = custom_message
                messages.warning(request, f"Variável {e} não encontrada - usando mensagem sem formatação")
            except Exception as e:
                formatted_message = custom_message
                print(f"DEBUG: Erro na formatação: {e}")
            
            telegram_success = send_telegram_alert_directly(formatted_message)
            
            alerta = AlertHistory.objects.create(
                math_model=math_model,
                station=station,
                alert_time=timezone.now(),
                alert_value=value,
                alert_message=formatted_message,
                details=f"Alerta manual - Valor: {value:.3f} | Temp: {temperature}°C | Umidade: {humidity}%",
                calculated_value=value
            )
            
            print(f"DEBUG: AlertHistory criado com ID: {alerta.id}")
            
            if telegram_success:
                messages.success(request, f"Alerta manual enviado com sucesso para {station.alias}!")
            else:
                messages.warning(request, "Alerta criado no histórico, mas houve problemas no envio do Telegram.")
            
            return redirect('dashboard:alert_history')
            
        except MathModel.DoesNotExist:
            messages.error(request, "Modelo matemático não encontrado.")
        except Station.DoesNotExist:
            messages.error(request, "Estação não encontrada.")
        except Exception as e:
            messages.error(request, f"Erro ao enviar alerta: {str(e)}")
            print(f"DEBUG: Erro geral: {e}")
            import traceback
            traceback.print_exc()
    
    math_models = MathModel.objects.filter(is_active=True)
    stations = Station.objects.all()
    
    context = {
        'math_models': math_models,
        'stations': stations,
    }
    
    return render(request, 'dashboard/send_manual_alert.html', context)

def send_telegram_alert_directly(message):
    try:
        usuarios = TelegramUser.objects.filter(is_active=True)
        
        if not usuarios.exists():
            print("Nenhum usuário cadastrado no Telegram")
            return False
        
        print(f"Enviando para {usuarios.count()} usuários")
        
        enviados = 0
        for usuario in usuarios:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {
                    'chat_id': usuario.chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                print(f"Enviando para chat_id: {usuario.chat_id}")
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    enviados += 1
                    print(f"Mensagem enviada para {usuario.first_name}")
                else:
                    print(f"Erro API Telegram: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Erro no envio para {usuario.chat_id}: {e}")
        
        print(f"Total enviados: {enviados}/{usuarios.count()}")
        return enviados > 0
        
    except Exception as e:
        print(f"Erro geral no envio Telegram: {e}")
        return False