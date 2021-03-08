from fyle.platform import Platform

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings


def get_or_none(model, **kwargs):
    try:
        model_object = model.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None
    return model_object


def get_fyle_sdk_connection(refresh_token):
    return Platform(
        server_url=settings.FYLE_PLATFORM_URL,
        token_url='{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL),
        client_id=settings.FYLE_CLIENT_ID,
        client_secret=settings.FYLE_CLIENT_SECRET,
        refresh_token=refresh_token
    )