from telegram import Bot, Update
from telegram.ext import MessageHandler, Filters


def echo(bot: Bot, update: Update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


echo_handler = MessageHandler(Filters.text, echo)
