import datetime
from urllib.parse import quote_plus

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

FYLE_BRANCHIO_BASE_URI = settings.FYLE_BRANCHIO_BASE_URI


def get_or_none(model, **kwargs):
    try:
        model_object = model.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None
    return model_object


def get_formatted_datetime(datetime_value, required_format):
    datetime_value = datetime.datetime.fromisoformat(datetime_value)
    formatted_datetime = datetime_value.strftime(required_format)
    return formatted_datetime


def convert_to_branchio_url(url):
    return '{}/branchio_redirect?redirect_uri={}'.format(FYLE_BRANCHIO_BASE_URI, quote_plus(url))
