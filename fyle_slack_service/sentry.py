from sentry_sdk import set_user

class Sentry:

    @staticmethod
    def traces_sampler(sampling_context):
        # avoiding ready APIs in performance tracing
        if sampling_context.get('wsgi_environ') is not None:
            if sampling_context['wsgi_environ']['PATH_INFO'] in ['/ready']:
                return 0

        return 0.2

    @staticmethod
    def set_user(user_id=None, team_id=None):
        set_user({
            'user_id': user_id,
            'team_id': team_id
        })
