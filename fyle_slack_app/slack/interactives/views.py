import json

from typing import Any, Callable, Dict, Optional
from slack_sdk.web import WebClient

from django.http.response import JsonResponse

from ...slack import SlackView
from ...models import Team
from ...libs import utils, assertions
from .block_action_handlers import BlockActionHandler


class SlackInteractiveView(SlackView, BlockActionHandler):

    slack_client: Optional[WebClient] = None
    slack_payload: Optional[Dict] = None
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    trigger_id: Optional[str] = None


    def _set_slack_client(self) -> None:
        slack_team = utils.get_or_none(Team, id=self.team_id)
        assertions.assert_found(slack_team, 'Slack team not registered')
        self.slack_client = WebClient(token=slack_team.bot_access_token)


    def post(self, request) -> JsonResponse:
        payload = request.POST.get('payload')
        slack_payload = json.loads(payload)

        # Extract details from payload
        self.slack_payload = slack_payload
        self.user_id = slack_payload['user']['id']
        self.team_id = slack_payload['team']['id']
        self.trigger_id = slack_payload['trigger_id']

        # Set slack client
        self._set_slack_client()

        event_type = slack_payload['type']

        # Check interactive event type and call it's respective handler
        if event_type == 'block_actions':
            # Call handler function from BlockActionHandler
            return self.handle_block_actions(self.slack_client, self.slack_payload, self.user_id, self.team_id)
    
        return JsonResponse({}, status=200)
