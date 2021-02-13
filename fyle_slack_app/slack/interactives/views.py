from fyle_slack_app.slack.authorization.tasks import get_slack_user_dm_channel_id
import json

from typing import Callable, Dict
from slack_sdk.web import WebClient

from django.http.response import JsonResponse
from django.contrib.sites.shortcuts import get_current_site

from ...slack import SlackView
from ...models import SlackTeam
from ...libs import utils
from .handlers import BlockActionHandler


class SlackInteractiveView(SlackView, BlockActionHandler):

    slack_client: WebClient = None
    slack_payload: Dict = None
    user_id: str = None
    team_id: str = None
    trigger_id: str = None
    slack_client: WebClient = None

    def _set_slack_client(self) -> None:
        slack_team = utils.get_or_none(SlackTeam, id=self.team_id)
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

        if event_type == 'block_actions':
            return self.handle_block_actions()
    
        return JsonResponse({}, status=200)
    

    def handle_invalid_block_actions(self) -> JsonResponse:
        user_dm_channel_id = get_slack_user_dm_channel_id(self.slack_client, self.user_id)
        self.slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Seems like something bad happened :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the block actions from slack
    def handle_block_actions(self) -> Callable:
        action_id = self.slack_payload['actions'][0]['action_id']
        handler = getattr(self, action_id, self.handle_invalid_block_actions)
        return handler(self.slack_client, self.slack_payload, self.user_id, self.team_id)
