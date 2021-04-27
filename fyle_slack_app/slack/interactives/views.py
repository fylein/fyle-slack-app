import json

from django.http import HttpRequest, JsonResponse

from fyle_slack_app.slack import SlackView
from fyle_slack_app.slack.interactives.block_action_handlers import BlockActionHandler


class SlackInteractiveView(SlackView, BlockActionHandler):

    def post(self, request: HttpRequest) -> JsonResponse:
        payload = request.POST.get('payload')
        slack_payload = json.loads(payload)

        # Extract details from payload
        user_id = slack_payload['user']['id']
        team_id = slack_payload['team']['id']

        # Set slack client
        self._set_slack_client(team_id)

        event_type = slack_payload['type']

        # Check interactive event type and call it's respective handler
        if event_type == 'block_actions':
            # Call handler function from BlockActionHandler
            return self.handle_block_actions(slack_payload, user_id, team_id)

        return JsonResponse({}, status=200)
