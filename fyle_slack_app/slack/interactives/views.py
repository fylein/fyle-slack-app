from fyle_slack_app.slack.authorization.tasks import get_slack_user_dm_channel_id
import json
import base64

from typing import Dict
from slack_sdk.web import WebClient

from django.conf import settings
from django.http.response import HttpResponseRedirect, JsonResponse
from django.contrib.sites.shortcuts import get_current_site

from fyle_slack_app.slack import SlackView
from fyle_slack_app.models import SlackTeam
from fyle_slack_app.libs import utils

class SlackInteractiveView(SlackView):

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
    
    # Handle all the block actions from slack
    def handle_block_actions(self):
        action_id = self.slack_payload['actions'][0]['action_id']
        
        if action_id == 'link_fyle_account':
            return self.link_fyle_account()
        
        return JsonResponse({}, status=200)
    

    def link_fyle_account(self):
        state_json = {
            'user_id': self.user_id,
            'team_id': self.team_id
        }
        state = json.dumps(state_json)

        encoded_state = state.encode()
        base64_encoded_state = base64.urlsafe_b64encode(encoded_state).decode()

        redirect_uri = '{}/fyle/authorization'.format(settings.SLACK_SERVICE_BASE_URL)

        FYLE_OAUTH_URL = 'https://accounts.fyle.tech/app/developers/#/oauth/authorize?client_id={}&response_type=code&state={}&redirect_uri={}'.format(
            settings.FYLE_CLIENT_ID,
            base64_encoded_state,
            redirect_uri
        )
        
        slack_user_dm_channel_id = get_slack_user_dm_channel_id(self.slack_client, self.user_id)
        
        self.slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            text=FYLE_OAUTH_URL
        )
        return HttpResponseRedirect(FYLE_OAUTH_URL)