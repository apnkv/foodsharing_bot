from telegram import Bot
from telegram.ext import Dispatcher
import logging

from django.conf import settings

from .handlers import echo_handler


log = logging.getLogger('foodsharing_bot.bot')


def setup(token):
    bot = Bot(token)
    if settings.TELEGRAM_BOT_WEBHOOK_ENABLED:
        bot.set_webhook(settings.TELEGRAM_BOT_WEBHOOK_URL)
        log.info('Bot set up.')
    # We will provide multithreading/caching etc. manually
    # (we'll have 4 workers anyway)
    dispatcher = Dispatcher(bot, None, workers=0)

    dispatcher.add_handler(echo_handler)

    return bot, dispatcher


bot, dispatcher = setup(settings.TELEGRAM_BOT_TOKEN)
