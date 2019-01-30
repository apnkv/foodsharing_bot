from ..taskapp.celery import app
from .models import Session, Offer
from django.core import files

import io
import requests
from slugify import slugify


@app.task
def create_offer(bot, item_name, item_description, giver_id,
                 contact_info, location_name, lat, lng, photo_file_id=None):
    offer = Offer.objects.create(
        item_name=item_name,
        item_description=item_description,
        giver=Session.objects.filter(telegram_user_id=giver_id).first(),
        contact_info=contact_info,
        location_name=location_name,
        lat=lat,
        lng=lng,
        status=Offer.RECEIVER_NOT_ASSIGNED,
    )

    if photo_file_id is not None:
        url = bot.get_file(photo_file_id)['file_path']
        extension = url[url.rfind('.'):]
        image = io.BytesIO(requests.get(url).content)
        name = f'{slugify(item_name)[:20]}_{photo_file_id[-8:]}{extension}'
        offer.photo.save(name, files.File(image))
        offer.save()
