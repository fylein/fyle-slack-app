from typing import Callable, Dict

from django.http.response import JsonResponse

from django_q.tasks import async_task

from fyle.platform import exceptions

from fyle_slack_app import tracking
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.fyle.utils import get_fyle_oauth_url, get_fyle_profile
from fyle_slack_app.models import User, NotificationPreference
from fyle_slack_app.slack.ui.dashboard import messages as dashboard_messages
from fyle_slack_app.slack.ui.notifications import preference_messages as notification_preference_messages
from fyle_slack_app.slack import utils as slack_utils


logger = logger.get_logger(__name__)


class SlackCommandHandler:

    _command_handlers: Dict = {}

    def _initialize_command_handlers(self):
        self._command_handlers = {
            'fyle_unlink_account': self.handle_fyle_unlink_account,
            'fyle_notification_preferences': self.handle_fyle_notification_preferences
        }

    def handle_invalid_command(self, user_id: str, team_id: str, user_dm_channel_id: str) -> JsonResponse:
        slack_client = slack_utils.get_slack_client(team_id)

        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Hey buddy, seems like you\'ve hit an invalid slack command :no_entry_sign:'
        )
        return JsonResponse({}, status=200)


    def handle_slack_command(self, command: str, user_id: str, team_id: str, user_dm_channel_id: str) -> Callable:

        # Initialize slack command handlers
        self._initialize_command_handlers()

        handler = self._command_handlers.get(command, self.handle_invalid_command)

        return handler(user_id, team_id, user_dm_channel_id)


    def handle_fyle_unlink_account(self, user_id: str, team_id: str, user_dm_channel_id: str) -> JsonResponse:
        async_task(
            'fyle_slack_app.slack.commands.tasks.fyle_unlink_account',
            user_id,
            team_id,
            user_dm_channel_id
        )
        return JsonResponse({}, status=200)


    def update_home_tab_with_pre_auth_message(self, user_id: str, team_id: str) -> None:
        slack_client = slack_utils.get_slack_client(team_id)

        user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(user_info['ok'] is True)

        fyle_oauth_url = get_fyle_oauth_url(user_id, team_id)

        pre_auth_message_view = dashboard_messages.get_pre_authorization_message(
            user_info['user']['real_name'],
            fyle_oauth_url
        )

        slack_client.views_publish(user_id=user_id, view=pre_auth_message_view)


    def handle_fyle_notification_preferences(self, user_id: str, team_id: str, user_dm_channel_id: str) -> JsonResponse:
        user = utils.get_or_none(User, slack_user_id=user_id)
        assertions.assert_found(user, 'Slack user not found')

        user_notification_preferences = NotificationPreference.objects.values('notification_type', 'is_enabled').filter(slack_user_id=user_id).order_by('-notification_type')

        try:
            fyle_profile = get_fyle_profile(user.fyle_refresh_token)

            notification_preference_blocks = notification_preference_messages.get_notification_preferences_blocks(user_notification_preferences, fyle_profile['roles'])

            slack_client = slack_utils.get_slack_client(team_id)

            slack_client.chat_postMessage(
                blocks=notification_preference_blocks,
                channel=user_dm_channel_id
            )
        except exceptions.NotFoundItemError as error:
            logger.info('Fyle profile not found for user %s - %s', user.slack_user_id, user.fyle_user_id)
            logger.info('API call error %s', error)

        return JsonResponse({}, status=200)


    def track_fyle_account_unlinked(self, user: User) -> None:
        event_data = {
            'asset': 'SLACK_APP',
            'slack_user_id': user.slack_user_id,
            'fyle_user_id': user.fyle_user_id,
            'email': user.email,
            'slack_team_id': user.slack_team.id,
            'slack_team_name': user.slack_team.name
        }

        tracking.identify_user(user.email)

        tracking.track_event(user.email, 'Fyle Account Unlinked From Slack', event_data)
