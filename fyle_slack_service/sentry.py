import sentry_sdk

from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk import capture_exception, capture_message

from django.conf import settings

class Sentry:

    @staticmethod
    def init():
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            send_default_pii=True,
            integrations=[DjangoIntegration()],
            server_name='slack-app',
            environment=settings.ENVIRONMENT,
            traces_sampler=Sentry.traces_sampler,
            attach_stacktrace=True
        )

    @staticmethod
    def traces_sampler(sampling_context):
        # avoiding ready APIs in performance tracing
        if sampling_context.get('wsgi_environ') is not None:
            if sampling_context['wsgi_environ']['PATH_INFO'] in ['/ready']:
                return 0

        return 0.2


    @staticmethod
    def capture_exception(message=None):
        error = Exception(message)
        capture_exception(error)
