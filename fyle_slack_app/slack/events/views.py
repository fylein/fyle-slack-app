import json

from django.http import JsonResponse, HttpRequest

from fyle_slack_app.slack import SlackView
from fyle_slack_app.slack.events.handlers import SlackEventHandler


class SlackEventView(SlackView, SlackEventHandler):

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

            self.handle_event_callback(subevent_type, slack_payload, team_id)

        return JsonResponse(event_response, status=200)
