from django.core.exceptions import ObjectDoesNotExist


def get_or_none(model, **kwargs):
    try:
        model_object = model.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None
    return model_object
