from typing import Callable, Dict

from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django_q.tasks import schedule, async_task
from django_q.models import Schedule

from fyle_slack_app.models import User
from fyle_slack_app.fyle.utils import get_fyle_oauth_url
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.slack.ui.dashboard import messages
from fyle_slack_app.slack import utils as slack_utils


logger = logger.get_logger(__name__)


class SlackEventHandler:

    _event_callback_handlers: Dict = {}

    def _initialize_event_callback_handlers(self):
        self._event_callback_handlers = {
            'team_join': self.handle_new_user_joined,
            'app_home_opened': self.handle_app_home_opened,
            'app_uninstalled': self.handle_app_uninstalled
        }


    def handle_invalid_event(self, slack_payload: Dict, team_id: str) -> JsonResponse:
        # No need to send any message to user in this case
        # Slack sends some message event whenever a message is sent to slack
        # Ex: Pre auth message
        # Since we're not interested in that & it will call this function to be invoked
        # So, do nothing in those cases
        return JsonResponse({}, status=200)


    def handle_event_callback(self, event_type: str, slack_payload: Dict, team_id: str) -> Callable:

        logger.info('Slack Event Received -> %s', event_type)

        self._initialize_event_callback_handlers()

        handler = self._event_callback_handlers.get(event_type, self.handle_invalid_event)

        return handler(slack_payload, team_id)


    def handle_app_uninstalled(self, slack_payload: Dict, team_id: str) -> JsonResponse:

        # Deleting team details in background task
        async_task(
            'fyle_slack_app.slack.events.tasks.uninstall_app',
            team_id
        )

        response = JsonResponse({}, status=200)

        # Passing this for slack not to retry `app_uninstalled` event again
        response['X-Slack-No-Retry'] = 1

        return response


    def handle_new_user_joined(self, slack_payload: Dict, team_id: str) -> None:
        user_id = slack_payload['event']['user']['id']
        schedule('fyle_slack_app.slack.events.tasks.new_user_joined_pre_auth_message',
                 user_id,
                 team_id,
                 schedule_type=Schedule.ONCE,
                 next_run=timezone.now() + timedelta(days=7)
                )


    def handle_app_home_opened(self, slack_payload: Dict, team_id: str) -> JsonResponse:
        user_id = slack_payload['event']['user']
        user = utils.get_or_none(User, slack_user_id=user_id)

        slack_client = slack_utils.get_slack_client(team_id)

        # User is not present i.e. user hasn't done Fyle authorization
        if user is not None:
            dashboard_view = messages.get_post_authorization_message()
        else:
            user_info = slack_client.users_info(user=user_id)
            assertions.assert_good(user_info['ok'] is True)

            fyle_oauth_url = get_fyle_oauth_url(user_id, team_id)

            dashboard_view = messages.get_pre_authorization_message(user_info['user']['real_name'], fyle_oauth_url)

        slack_client.views_publish(user_id=user_id, view=dashboard_view)

        return JsonResponse({}, status=200)
