from django.http.response import JsonResponse

from fyle_slack_app.libs import utils
from fyle_slack_app.models import User
from fyle_slack_app.fyle.authorization.views import FyleAuthorization


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
            FyleAuthorization().update_home_tab_with_pre_auth_message(slack_client, user_id, team_id)

        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text=text
        )
        return JsonResponse({}, status=200)
