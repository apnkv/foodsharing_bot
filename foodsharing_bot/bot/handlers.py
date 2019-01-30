from telegram import Bot, Update
from telegram.ext import MessageHandler, Filters, ConversationHandler, CommandHandler
from telegram import ReplyKeyboardMarkup

import telegram as tg
import logging
import redis

from ..core.models import Session, Offer
from ..core.tasks import create_offer


log = logging.getLogger('foodsharing_bot.bot.handlers')
store = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)


FIRST_NAME, LAST_NAME, EMAIL, GIVE_OR_TAKE, TAKE_LOCATION, GIVE_OFFER_ITEM_NAME, GIVE_OFFER_ITEM_DESCRIPTION,\
    GIVE_OFFER_LOCATION_NAME, GIVE_OFFER_CONTACT, GIVE_OFFER_LOCATION, GIVE_OFFER_UPLOAD_PHOTO,\
    GIVE_OFFER_REVIEW = range(12)


def _get_user_and_chat_ids(update):
    return update.message.from_user['id'], update.message.chat.id


def echo(bot: Bot, update: Update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


def action_keyboard(bot: Bot, update: Update):
    reply_markup = ReplyKeyboardMarkup([['Взять еду', 'Отдать еду']], one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id, text="Что ты хочешь сделать?", reply_markup=reply_markup)

    return GIVE_OR_TAKE


def start(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    session = Session.objects.filter(telegram_chat_id=chat_id).first()
    if session is not None:
        update.message.reply_text(
            f'Привет, {session.name}!'
        )

        return action_keyboard(bot, update)
    else:
        update.message.reply_text(
            'Привет! Я бот для фудшеринга. Мы видимся в первый раз. '
            'Как тебя зовут?'
        )

        return FIRST_NAME


def cancel(bot: Bot, update: Update):
    update.message.reply_text(
        'Еще увидимся!'
    )

    return ConversationHandler.END


def give_or_take(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    if update.message.text == 'Взять еду':
        bot.send_message(
            chat_id,
            'Хорошо. Мне нужно знать, где ты находишься, и я покажу, какую еду предлагают рядом.'
        )
        update.message.reply_text(
            'Скинь свою локацию в сообщении.'
        )

        return TAKE_LOCATION

    elif update.message.text == 'Отдать еду':

        store.hset(f'fsbot_chat_{chat_id}_offer', 'completed', 0)

        bot.send_message(
            chat_id,
            'Хорошо! Назови, пожалуйста, что ты хочешь отдать.'
        )

        return GIVE_OFFER_ITEM_NAME

    return ConversationHandler.END


def take_location(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    location = update.message.location

    return ConversationHandler.END


def give_offer_item_name(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    item_name = update.message.text
    store.hset(f'fsbot_chat_{chat_id}_offer', 'item_name', item_name)

    update.message.reply_text(
        'Спасибо! Теперь коротко опиши этот предмет — вид, состояние, почему хочешь отдать.'
    )

    return GIVE_OFFER_ITEM_DESCRIPTION


def give_offer_item_description(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    item_description = update.message.text
    store.hset(f'fsbot_chat_{chat_id}_offer', 'item_description', item_description)

    update.message.reply_text(
        f'Отлично! Напиши, какой адрес мне показывать желающим забрать эту еду.'
    )

    return GIVE_OFFER_LOCATION_NAME


def give_offer_location_name(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    location_name = update.message.text
    store.hset(f'fsbot_chat_{chat_id}_offer', 'location_name', location_name)

    print(update.message.from_user)

    try:
        username = update.message.from_user['username']
    except KeyError:
        username = None

    if username == '':
        username = None

    keyboard = ReplyKeyboardMarkup([[f'@{username}']], one_time_keyboard=True)

    bot.send_message(
        chat_id,
        f'Осталось совсем немного. Оставь свой юзернейм в телеграме или номер телефона.',
        reply_markup=keyboard if username is not None else None
    )

    return GIVE_OFFER_CONTACT


def give_offer_contact(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    contact = update.message.text
    store.hset(f'fsbot_chat_{chat_id}_offer', 'contact_info', contact)

    location_button = tg.KeyboardButton(text='Отправить текущую локацию', request_location=True)
    location_keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True)

    bot.send_message(
        chat_id,
        f'Теперь, пожалуйста, прикрепи точную локацию, чтобы я мог добавить твое предложение в поиск.',
        reply_markup=location_keyboard
    )

    return GIVE_OFFER_LOCATION


def give_offer_actual_location(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    location = update.message.location
    lat = location.latitude
    lng = location.longitude

    pipe = store.pipeline()
    pipe.hset(f'fsbot_chat_{chat_id}_offer', 'lat', lat)
    pipe.hset(f'fsbot_chat_{chat_id}_offer', 'lng', lng)

    keyboard = ReplyKeyboardMarkup([['Без фотографии']], one_time_keyboard=True)

    bot.send_message(
        chat_id,
        'Спасибо! Теперь отправь фотографию своего предложения.',
        reply_markup=keyboard
    )

    return GIVE_OFFER_UPLOAD_PHOTO


def give_offer_upload_photo(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    photo = getattr(update.message, 'photo', None)

    if photo is None:
        store.hset(f'fsbot_chat_{chat_id}_offer', 'photo_id', None)
    else:
        store.hset(f'fsbot_chat_{chat_id}_offer', 'photo_id', photo[-1].file_id)

    offer = store.hgetall(f'fsbot_chat_{chat_id}_offer')

    bot.send_message(chat_id, 'Спасибо!')
    bot.send_message(
        chat_id,
        f'Давай еще раз посмотрим на твое предложение:\n\n'
        f'*Название*: {offer["item_name"]}\n'
        f'*Описание*: {offer["item_description"]}\n'
        f'*Адрес*: {offer["location_name"]}\n'
        f'*Местоположение*: {offer["lat"]}, {offer["lng"]}\n'
        f'*Контакт*: {offer["contact"]}',
        parse_mode=tg.ParseMode.MARKDOWN
    )

    keyboard = ReplyKeyboardMarkup([['Все правильно']], one_time_keyboard=True)

    if photo is not None:
        bot.send_photo(chat_id, photo[-1].file_id, reply_markup=keyboard)

    return GIVE_OFFER_REVIEW


def give_offer_review(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    if update.message.text == 'Все правильно':
        bot.send_message(
            chat_id,
            'Супер! Скоро я опубликую твое предложение.'
        )
        offer = store.hgetall(f'fsbot_chat_{chat_id}_offer')
        create_offer.delay(
            bot=bot,
            item_name=offer['item_name'],
            item_description=offer['item_description'],
            giver_id=user_id,
            contact_info=offer['contact_info'],
            location_name=offer['location_name'],
            photo_file_id=offer['photo_id'] if offer['photo_id'] is not None else None,
            lat=offer['lat'],
            lng=offer['lng'],
        )
        return action_keyboard(bot, update)
    else:
        bot.send_message(
            chat_id,
            'Пока предложение нельзя изменять, но скоро я обязательно научусь.'
        )
        return GIVE_OFFER_REVIEW


def first_name(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    session = Session.objects.create(
        telegram_chat_id=chat_id,
        telegram_user_id=user_id,
        name=update.message.text
    )

    store.hset(f'fsbot_chat_{chat_id}', 'name', session.name)

    update.message.reply_text(
        f'Очень приятно, {update.message.text}!'
    )

    return action_keyboard(bot, update)


echo_handler = MessageHandler(Filters.text, echo)
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        FIRST_NAME: [MessageHandler(Filters.text, first_name)],
        GIVE_OR_TAKE: [MessageHandler(Filters.text, give_or_take)],
        TAKE_LOCATION: [MessageHandler(Filters.location, take_location)],
        GIVE_OFFER_ITEM_NAME: [MessageHandler(Filters.text, give_offer_item_name)],
        GIVE_OFFER_ITEM_DESCRIPTION: [MessageHandler(Filters.text, give_offer_item_description)],
        GIVE_OFFER_LOCATION_NAME: [MessageHandler(Filters.text, give_offer_location_name)],
        GIVE_OFFER_CONTACT: [MessageHandler(Filters.text, give_offer_contact)],
        GIVE_OFFER_LOCATION: [MessageHandler(Filters.location, give_offer_actual_location)],
        GIVE_OFFER_UPLOAD_PHOTO: [MessageHandler((Filters.photo | Filters.text), give_offer_upload_photo)],
        GIVE_OFFER_REVIEW: [MessageHandler(Filters.text, give_offer_review)],
    },

    fallbacks=[CommandHandler('cancel', cancel)]
)
