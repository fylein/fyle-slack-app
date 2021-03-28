import analytics

from django.conf import settings


analytics.write_key = settings.FYLE_SLACK_APP_SEGMENT_KEY

def identify_user(user_email) -> bool:
    analytics.identify(user_email, {})
    return True


def track_event(user_email, event_name, event_data) -> bool:
    analytics.track(user_email, event_name, event_data)
    return True
