import os
import sentry_sdk

from sentry_sdk import set_user, capture_exception
from sentry_sdk.integrations.django import DjangoIntegration

from django.conf import settings


class Sentry:

    @staticmethod
    def sentry_before_send(event, hint):
        if 'exc_info' in hint:
            return event
        return None

    @staticmethod
    def traces_sampler(sampling_context):
        # avoiding ready APIs in performance tracing
        if sampling_context.get('wsgi_environ') is not None:
            if sampling_context['wsgi_environ']['PATH_INFO'] in ['/ready']:
                return 0

        return 0.2

    @staticmethod
    def init():
        if settings.SENTRY_DSN is not None:
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[DjangoIntegration()],
                traces_sampler=Sentry.traces_sampler,
                server_name='slack-app',
                environment=settings.ENVIRONMENT,
                before_send=Sentry.sentry_before_send
            )

    @staticmethod
    def set_sentry_user(user_remote_address, user_details=None):
        sentry_details = {
            'ip_address': user_remote_address
        }
        if user_details is not None:
            sentry_details['user_details'] = user_details

        set_user(sentry_details)

    @staticmethod
    def capture_sentry_exception(error=None):
        capture_exception(error)
