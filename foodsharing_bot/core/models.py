from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from ..users.models import User


class Session(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bot_sessions', blank=True, null=True)
    telegram_chat_id = models.IntegerField(blank=False, null=False, db_index=True)
    telegram_user_id = models.IntegerField(blank=True, null=True, db_index=True)
    name = models.CharField(max_length=255, blank=False, null=False)

    def __str__(self):
        return f'{self.name} (User {self.telegram_user_id}, chat {self.telegram_chat_id})'


class OfferManager(models.Manager):
    pass


class Offer(TimeStampedModel):
    RECEIVER_NOT_ASSIGNED = 0
    RECEIVER_PENDING = 1
    RECEIVER_CONFIRMED = 2
    COMPLETED = 3

    STATUS_CHOICES = (
        (RECEIVER_NOT_ASSIGNED, _('Receiver not assigned')),
        (RECEIVER_PENDING, _('Receiver pending')),
        (RECEIVER_CONFIRMED, _('Receiver confirmed')),
        (COMPLETED, _('Completed'))
    )

    item_name = models.CharField(verbose_name=_('item name'),
                                 max_length=256,
                                 null=False, blank=False)

    item_description = models.TextField(verbose_name=_('description'),
                                        null=True, blank=True)

    giver = models.ForeignKey(to=Session,
                              verbose_name='giver',
                              on_delete=models.SET_NULL,
                              related_name='given_offers',
                              null=True, blank=False)

    receiver = models.ForeignKey(to=Session,
                                 verbose_name='receiver',
                                 on_delete=models.SET_NULL,
                                 related_name='received_offers',
                                 null=True, blank=False)

    contact_info = models.TextField(verbose_name=_('contact information'), null=True, blank=True)

    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, null=False, blank=False)

    photo = models.ImageField(upload_to='photos', verbose_name=_('photo'), null=True, blank=True)

    comment = models.TextField(verbose_name=_('comment'), null=True, blank=True)

    location_name = models.CharField(verbose_name=_('location'), max_length=500,
                                     null=True, blank=False)

    lat = models.DecimalField(verbose_name=_('latitude'), max_digits=9, decimal_places=6)
    lng = models.DecimalField(verbose_name=_('longitude'), max_digits=9, decimal_places=6)

    def __str__(self):
        return f'{self.item_name} — {self.giver.name} ({self.giver.telegram_user_id})'
