from typing import Any, Dict, Union, Callable

import base64
import datetime
import json
import hashlib
import string
import random

from functools import wraps
from urllib.parse import quote_plus, urlencode

from django.core.cache import cache
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
    # Enable support for parsing arbitrary ISO 8601 strings ('Z' strings specifically)
    datetime_value = datetime_value.replace('Z', '')

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


def get_hashed_args(*factors) -> str:
    args = json.dumps(factors, sort_keys=True)
    hashed_args = hashlib.md5(args.encode('utf-8'))
    return hashed_args.hexdigest()


def generate_random_string(string_length=10):
    """Generate a random string of fixed length """
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(string_length))


# Default timeout for cache is 60 seconds
def cache_this(timeout: int = None) -> Callable:
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def function_wrapper(*args: Any, **kwargs: Any) -> Callable:

            if timeout is None:
                raise Exception('Timeout not specified for caching')

            # Creating hash of the function arguments passed
            hashed_args = get_hashed_args(args, kwargs)

            # Creating a cache key with prefix as function name
            # and suffix as hashed function arguments
            cache_key = '{}.{}'.format(function.__name__, hashed_args)

            response = cache.get(cache_key)

            # If cache doesn't return anything call the original function
            # and cache the function response
            if response is None:
                response = function(*args, **kwargs)
                cache.set(cache_key, response, timeout)

            return response
        return function_wrapper
    return decorator
