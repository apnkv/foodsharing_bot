from telegram import Bot
from telegram.ext import Dispatcher
import logging
import redis

from django.conf import settings

from .handlers import conv_handler


log = logging.getLogger('foodsharing_bot.bot')


def setup(token):
    bot = Bot(token)
    if settings.TELEGRAM_BOT_WEBHOOK_ENABLED:
        bot.set_webhook(settings.TELEGRAM_BOT_WEBHOOK_URL)
        log.info('Bot set up.')

    dispatcher = Dispatcher(bot, None, workers=0)

    dispatcher.add_handler(conv_handler)

    return bot, dispatcher


bot, dispatcher = setup(settings.TELEGRAM_BOT_TOKEN)
