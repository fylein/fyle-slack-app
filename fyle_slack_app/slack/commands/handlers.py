from django.http.response import JsonResponse

from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.slack.utils import get_fyle_oauth_url
from fyle_slack_app.models import User
from fyle_slack_app.slack.ui.dashboard import messages as dashboard_messages


class SlackCommandHandler:

    _command_handlers = {}

    def _initialize_command_handlers(self):
        self._command_handlers = {
            'fyle_unlink_account': self.handle_fyle_unlink_account
        }


    def handle_invalid_command(self, slack_client, user_id, team_id, user_dm_channel_id):
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Hey buddy, seems like you\'ve hit an invalid slack command :no_entry_sign:'
        )
        return JsonResponse({}, status=200)


    def handle_slack_command(self, command, slack_client, user_id, team_id, user_dm_channel_id):

        # Initialize slack command handlers
        self._initialize_command_handlers()

        handler = self._command_handlers.get(command, self.handle_invalid_command)

        return handler(slack_client, user_id, team_id, user_dm_channel_id)


    def handle_fyle_unlink_account(self, slack_client, user_id, team_id, user_dm_channel_id):
        user = utils.get_or_none(User, slack_user_id=user_id)

        # Text message if user hasn't linked Fyle account
        text = 'Hey buddy, you haven\'t linked your Fyle account yet :face_with_head_bandage: \n' \
            'Checkout home tab for `Link Your Fyle Account` to link your Slack with Fyle :zap:'

        if user is not None:
            # Deleting user entry to unlink fyle account
            user.delete()
            # pylint: disable=line-too-long
            text = 'Hey, you\'ve successfully unlinked your Fyle account with slack :white_check_mark:\n ' \
                'If you change your mind about us checkout home tab for `Link Your Fyle Account` to link your Slack with Fyle :zap:'

            # Update home tab with pre auth message
            self.update_home_tab_with_pre_auth_message(slack_client, user_id, team_id)

        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text=text
        )
        return JsonResponse({}, status=200)


    def update_home_tab_with_pre_auth_message(self, slack_client, user_id, team_id):
        user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(user_info['ok'] is True)

        fyle_oauth_url = get_fyle_oauth_url(user_id, team_id)

        pre_auth_message_view = dashboard_messages.get_pre_authorization_message(
            user_info['user']['real_name'],
            fyle_oauth_url
        )

        slack_client.views_publish(user_id=user_id, view=pre_auth_message_view)
