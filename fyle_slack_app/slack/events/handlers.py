from django.http import JsonResponse

from ...models import Team
from ...slack.utils import get_slack_user_dm_channel_id
from ...libs import utils, assertions


class SlackEventHandler:

    def _initialize_event_callback_handlers(self):
        self._event_callback_handlers = {
            'app_uninstalled': self.handle_app_uninstalled
        }


    def handle_invalid_event(self, slack_client, slack_payload, user_id, team_id):
        # No need to send any message to user in this case
        # Slack sends some message event whenever a message is sent to slack
        # Ex: Pre auth message
        # Since we're not interested in that & it will call this function to be invoked
        # So, do nothing in those cases
        return JsonResponse({}, status=200)


    def handle_event_callback(self, slack_client, event_type, slack_payload, team_id):

        self._initialize_event_callback_handlers()

        # Need to do this way since some of the events don't send user_id
        # Ex: Slack app_uninstalled event
        user_id = slack_payload.get('event').get('user')

        handler = self._event_callback_handlers.get(event_type, self.handle_invalid_event)

        return handler(slack_client, slack_payload, user_id, team_id)


    def handle_app_uninstalled(self, slack_client, slack_payload, user_id, team_id):
        team = utils.get_or_none(Team, id=team_id)
        assertions.assert_found(team, 'Slack team not registered')

        # Deleting team :)
        team.delete()

        return JsonResponse({}, status=200)
