from typing import Callable, Dict

from django.http import JsonResponse

from fyle_slack_app.models import NotificationPreference, User
from fyle_slack_app.libs import assertions, utils, logger
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.ui.notification_preferences import messages as notification_preference_messages


logger = logger.get_logger(__name__)


class ShortcutHandler:

    _shortcut_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_shortcut_handlers(self):
        self._shortcut_handlers = {
            'notification_preferences': self.handle_notification_preferences
        }


    # Gets called when function with an action is not found
    def _handle_invalid_shortcuts(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        slack_client = slack_utils.get_slack_client(team_id)

        user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Seems like something bad happened :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the shortcuts from slack
    def handle_shortcuts(self, slack_payload: Dict, user_id: str, team_id: str) -> Callable:
        '''
            Check if any function is associated with the action
            If present handler will call the respective function
            If not present call `handle_invalid_shortcuts` to send a prompt to user
        '''

        # Initialize handlers
        self._initialize_shortcut_handlers()

        callback_id = slack_payload['callback_id']

        handler = self._shortcut_handlers.get(callback_id, self._handle_invalid_shortcuts)

        return handler(slack_payload, user_id, team_id)


    def handle_notification_preferences(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        user = utils.get_or_none(User, slack_user_id=user_id)
        assertions.assert_found(user, 'Slack user not found')

        slack_client = slack_utils.get_slack_client(team_id)

        user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)

        user_notification_preferences = NotificationPreference.objects.values_list('notification_type', flat=True).filter(slack_user_id=user_id)

        notification_preference_blocks = notification_preference_messages.get_notification_preferences_blocks(user_notification_preferences)

        slack_client.chat_postMessage(
            blocks=notification_preference_blocks,
            channel=user_dm_channel_id
        )
        return JsonResponse({}, status=200)
