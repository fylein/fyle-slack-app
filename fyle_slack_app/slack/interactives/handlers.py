import base64
import json

from typing import Dict
from slack_sdk.web.client import WebClient

from django.conf import settings
from django.http.response import JsonResponse

from fyle_slack_app.slack.authorization.tasks import get_slack_user_dm_channel_id

class BlockActionHandler():

    def link_fyle_account(self, slack_client: WebClient, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        state_json = {
            'user_id': user_id,
            'team_id': team_id
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
        
        slack_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)
        
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            text=FYLE_OAUTH_URL
        )
        return JsonResponse({}, status=200)
