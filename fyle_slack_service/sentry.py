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
