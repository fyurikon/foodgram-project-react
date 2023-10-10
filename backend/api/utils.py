from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError


def get_object_or_bad_request(klass, *args, **kwargs):
    """
    This method was created to satisfy some API tests from
    postman collection. Some tests, in some situations
    want to get 400 instead of 404.
    """
    try:
        return get_object_or_404(klass, *args, **kwargs)
    except Http404:
        raise ValidationError('Объекта не существует!')
