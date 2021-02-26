from django.http import JsonResponse

from ...models import Team, User
from ...slack.utils import get_fyle_oauth_url
from ...libs import utils, assertions
from ..ui.dashboard import messages


class SlackEventHandler:

    def _initialize_event_callback_handlers(self):
        self._event_callback_handlers = {
            'app_uninstalled': self.handle_app_uninstalled,
            'app_home_opened': self.handle_app_home_opened
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


    def handle_app_home_opened(self, slack_client, slack_payload, user_id, team_id):
        user = utils.get_or_none(User, slack_user_id=user_id)

        # User is not present i.e. user hasn't done Fyle authorization
        if user is not None:
            dashboard_view = messages.get_post_authorization_message()
        else:
            user_info = slack_client.users_info(user=user_id)
            assertions.assert_good(user_info['ok'] == True)

            fyle_oauth_url = get_fyle_oauth_url(user_id, team_id)

            dashboard_view = messages.get_pre_authorization_message(user_info['user']['real_name'], fyle_oauth_url)

        slack_client.views_publish(user_id=user_id, view=dashboard_view)

        return JsonResponse({}, status=200)
