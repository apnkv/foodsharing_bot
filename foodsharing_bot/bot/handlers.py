from telegram import Bot, Update
from telegram.ext import MessageHandler, Filters, ConversationHandler, CommandHandler
from telegram import ReplyKeyboardMarkup

import telegram as tg
import logging
import redis

from ..core.models import Session, Offer
from ..core.tasks import create_offer
from ..core.utils import distance

import foodsharing_bot.bot.messages as messages


log = logging.getLogger('foodsharing_bot.bot.handlers')
store = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)


FIRST_NAME, LAST_NAME, EMAIL, GIVE_OR_TAKE, TAKE_LOCATION, GIVE_OFFER_ITEM_NAME, GIVE_OFFER_ITEM_DESCRIPTION,\
    GIVE_OFFER_LOCATION_NAME, GIVE_OFFER_CONTACT, GIVE_OFFER_LOCATION, GIVE_OFFER_UPLOAD_PHOTO,\
    GIVE_OFFER_REVIEW, TAKE_OFFER_DETAIL = range(13)


def _get_user_and_chat_ids(update):
    return update.message.from_user['id'], update.message.chat.id


def echo(bot: Bot, update: Update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


def action_keyboard(bot: Bot, update: Update):
    reply_markup = ReplyKeyboardMarkup([[messages.TAKE_FOOD, messages.GIVE_FOOD]],
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text=messages.WHAT_DO_YOU_WANT_TO_DO,
                     reply_markup=reply_markup)

    return GIVE_OR_TAKE


def start(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    session = Session.objects.filter(telegram_chat_id=chat_id).first()
    if session is not None:
        update.message.reply_text(
            messages.RECURRING_GREETING.format(session.name)
        )

        return action_keyboard(bot, update)
    else:
        update.message.reply_text(
            messages.FIRST_GREETING
        )

        return FIRST_NAME


def cancel(bot: Bot, update: Update):
    update.message.reply_text(
        messages.SEE_YOU
    )

    return ConversationHandler.END


def give_or_take(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    if update.message.text == messages.TAKE_FOOD:
        bot.send_message(
            chat_id,
            messages.OKAY_I_NEED_TO_KNOW_WHERE_YOU_ARE
        )
        bot.send_message(
            chat_id,
            messages.SEND_ME_YOUR_LOCATION,
            reply_markup=ReplyKeyboardMarkup(
                [[tg.KeyboardButton(messages.SEND_CURRENT_LOCATION, request_location=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        return TAKE_LOCATION

    elif update.message.text == messages.GIVE_FOOD:

        store.hset(f'fsbot_chat_{chat_id}_offer', 'completed', 0)

        bot.send_message(
            chat_id,
            messages.OKAY_NAME_YOUR_OFFER
        )

        return GIVE_OFFER_ITEM_NAME

    else:

        bot.send_message(
            chat_id,
            messages.CHOOSE_FROM_THE_KEYBOARD
        )

        return GIVE_OR_TAKE


def take_location(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    if update.message.text == 'Вернуться к началу':
        return action_keyboard(bot, update)

    location = update.message.location
    lat = location.latitude
    lng = location.longitude

    bot.send_message(
        chat_id,
        'Спасибо! Сейчас я поищу, что есть рядом с тобой.'
    )

    near_offers = Offer.objects.near(lat, lng)
    print(near_offers)

    if near_offers.count() > 0:

        keyboard = []
        for i, offer in enumerate(near_offers):
            keyboard.append([
                tg.InlineKeyboardButton(
                    f'{i + 1}. {offer.item_name} ({distance(lat, lng, float(offer.lat), float(offer.lng)):.2} км)',
                    callback_data=i
                )
            ])

        bot.send_message(
            chat_id,
            'Вот что я нашел:',
            reply_markup=tg.InlineKeyboardMarkup(keyboard)
        )
        return TAKE_OFFER_DETAIL
    else:
        keyboard = [[tg.KeyboardButton('Отправить текущее местоположение', request_location=True)],
                    ['Вернуться к началу']]

        bot.send_message(
            chat_id,
            'К сожалению, в радиусе 10 километров ничего нет. Можем попробовать поискать в другом месте. '
            'Скинь локацию еще раз.',
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )

        return TAKE_LOCATION


def take_offer_detail(bot: Bot, update: Update):
    pass


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

    keyboard = ReplyKeyboardMarkup([[f'@{username}']], one_time_keyboard=True, resize_keyboard=True)

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
    location_keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)

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

    keyboard = ReplyKeyboardMarkup([['Без фотографии']], one_time_keyboard=True, resize_keyboard=True)

    bot.send_message(
        chat_id,
        'Спасибо! Теперь отправь фотографию своего предложения.',
        reply_markup=keyboard
    )

    return GIVE_OFFER_UPLOAD_PHOTO


def give_offer_upload_photo(bot: Bot, update: Update):
    user_id, chat_id = _get_user_and_chat_ids(update)

    photo = getattr(update.message, 'photo', None)

    if (photo is None) or update.message.text == 'Без фотографии':
        store.hset(f'fsbot_chat_{chat_id}_offer', 'photo_id', 'None')
        photo = None
    else:
        store.hset(f'fsbot_chat_{chat_id}_offer', 'photo_id', photo[-1].file_id)

    offer = store.hgetall(f'fsbot_chat_{chat_id}_offer')

    bot.send_message(chat_id, 'Спасибо!')
    keyboard = ReplyKeyboardMarkup([['Все правильно']], one_time_keyboard=True, resize_keyboard=True)
    bot.send_message(
        chat_id,
        f'Давай еще раз посмотрим на твое предложение:\n\n'
        f'*Название*: {offer["item_name"]}\n'
        f'*Описание*: {offer["item_description"]}\n'
        f'*Адрес*: {offer["location_name"]}\n'
        f'*Местоположение*: {offer["lat"]}, {offer["lng"]}\n'
        f'*Контакт*: {offer["contact"]}',
        parse_mode=tg.ParseMode.MARKDOWN,
        reply_markup=None if photo is not None else keyboard
    )

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
            photo_file_id=offer['photo_id'] if offer['photo_id'] != 'None' else None,
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
        TAKE_LOCATION: [MessageHandler((Filters.location | Filters.text), take_location)],
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
