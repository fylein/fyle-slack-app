from typing import Any, Union

import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.base import Model


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
