import json

from typing import Callable, Dict, Optional
from slack_sdk.web import WebClient

from django.http.response import JsonResponse

from ...slack import SlackView
from ...models import Team
from ...slack.authorization.tasks import get_slack_user_dm_channel_id
from ...libs import utils
from .block_action_handlers import BlockActionHandler


class SlackInteractiveView(SlackView, BlockActionHandler):

    slack_client: Optional[WebClient] = None
    slack_payload: Optional[Dict] = None
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    trigger_id: Optional[str] = None


    def _set_slack_client(self) -> None:
        slack_team = utils.get_or_none(Team, id=self.team_id)
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
            return self._handle_block_actions()
    
        return JsonResponse({}, status=200)
    
    # Gets called when function with an action is not found
    def _handle_invalid_block_actions(self, slack_client, slack_payload, user_id, team_id) -> JsonResponse:
        user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Seems like something bad happened :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the block actions from slack
    def _handle_block_actions(self) -> Callable:
        '''
            Check if any function is associated with the action
            If present handler will call the respective function from `BlockActionHandler`
            If not present call `handle_invalid_block_actions` to send a prompt to user
        '''
        action_id = self.slack_payload['actions'][0]['action_id']
        handler = getattr(self, action_id, self._handle_invalid_block_actions)
        return handler(self.slack_client, self.slack_payload, self.user_id, self.team_id)
