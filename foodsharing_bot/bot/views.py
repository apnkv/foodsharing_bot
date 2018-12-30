from django.views import View
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest

import json
from telegram import Update

from .bot import bot
from .bot import dispatcher as bot_dispatcher


class MessageReceiveView(View):
    def post(self, request):

        # Check if the request comes from Telegram servers and the token is valid
        uri = request.build_absolute_uri()
        if not uri[:-1].endswith(settings.TELEGRAM_BOT_TOKEN)\
           and not uri.endswith(settings.TELEGRAM_BOT_TOKEN):
            return HttpResponseForbidden('Invalid token')

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except ValueError:
            return HttpResponseBadRequest('Malformed request body')

        update = Update.de_json(payload, bot)
        bot_dispatcher.process_update(update)

        return JsonResponse({}, status=200)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(MessageReceiveView, self).dispatch(request, *args, **kwargs)
