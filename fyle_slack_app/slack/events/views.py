import json

from slack_sdk.web import WebClient

from django.http import JsonResponse, HttpRequest

from fyle_slack_app.slack import SlackView
from fyle_slack_app.models import Team
from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.slack.events.handlers import SlackEventHandler


class SlackEventView(SlackView, SlackEventHandler):

    slack_client: WebClient = None

    def _set_slack_client(self, team_id: str) -> None:
        slack_team = utils.get_or_none(Team, id=team_id)
        assertions.assert_found(slack_team, 'Slack team not registered')
        self.slack_client = WebClient(token=slack_team.bot_access_token)


    def post(self, request: HttpRequest) -> JsonResponse:
        slack_payload = json.loads(request.body)

        event_type = slack_payload['type']

        event_response = {}
        # This event is required by slack during our slack event endpoint registering in slack settings
        # When adding endpoint it expects a challenge in response
        # If challenge is not received endpoint is not registered
        if event_type == 'url_verification':
            event_response = {'challenge': slack_payload['challenge']}

        elif event_type == 'event_callback':
            # Events of our interest come under event_callback from slack
            subevent_type = slack_payload['event']['type']
            team_id = slack_payload['team_id']

            # Set slack client
            self._set_slack_client(team_id)

            self.handle_event_callback(self.slack_client, subevent_type, slack_payload, team_id)

        return JsonResponse(event_response, status=200)
