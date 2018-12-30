from django.urls import path
from django.conf import settings
from . import views


app_name = 'bot'

urlpatterns = [
    path(f'{settings.TELEGRAM_BOT_TOKEN}/', views.MessageReceiveView.as_view(), name='message_receive'),
]
