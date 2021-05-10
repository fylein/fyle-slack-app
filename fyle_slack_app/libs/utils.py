from typing import Any, Dict, Union

import base64
import datetime
import json

from urllib.parse import quote_plus, urlencode

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db.models.base import Model

FYLE_BRANCHIO_BASE_URI = settings.FYLE_BRANCHIO_BASE_URI


def get_or_none(model: Model, **kwargs: Any) -> Union[None, Model]:
    try:
        model_object = model.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None
    return model_object


def get_formatted_datetime(datetime_value: datetime, required_format: str) -> str:
    datetime_value = datetime.datetime.fromisoformat(datetime_value)
    formatted_datetime = datetime_value.strftime(required_format)
    return formatted_datetime


def convert_to_branchio_url(url: str, query_params: Dict = None) -> str:
    branchio_url = '{}/branchio_redirect?redirect_uri={}'.format(FYLE_BRANCHIO_BASE_URI, quote_plus(url))
    if query_params is not None:
        encoded_query_params = urlencode(query_params)
        branchio_url = '{}?{}'.format(branchio_url, encoded_query_params)
    return branchio_url


def encode_state(state_params: Dict) -> str:
    state = json.dumps(state_params)

    encoded_state = state.encode()
    base64_encoded_state = base64.urlsafe_b64encode(encoded_state).decode()

    return base64_encoded_state


def decode_state(state: str) -> Dict:
    decoded_state = base64.urlsafe_b64decode(state.encode())
    state_params = json.loads(decoded_state.decode())
    return state_params
