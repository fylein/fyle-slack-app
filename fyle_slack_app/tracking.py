from mixpanel import Mixpanel

from django.conf import settings

FYLE_SLACK_APP_MIXPANEL_TOKEN = settings.FYLE_SLACK_APP_MIXPANEL_TOKEN

mixpanel_client = Mixpanel(FYLE_SLACK_APP_MIXPANEL_TOKEN)


def identify_user(user_email) -> bool:
    mixpanel_client.people_set(user_email, {})
    return True


def track_event(user_email, event_name, event_data) -> bool:
    mixpanel_client.track(user_email, event_name, event_data)
    return True
