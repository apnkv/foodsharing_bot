from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, IntegerField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = CharField(_("Name of User"), blank=True, max_length=255)
    telegram_user_id = IntegerField(_('Telegram ID'), blank=True, null=True)
    telegram_username = CharField(_('Telegram username'), blank=True, null=True, max_length=100)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})
