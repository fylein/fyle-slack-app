from typing import Dict, List

import json
import base64


from django.conf import settings

from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from fyle_slack_app.libs import assertions


def get_slack_user_dm_channel_id(slack_client: WebClient, user_id: str) -> str:
    slack_user_dm_channel_id = slack_client.conversations_open(users=[user_id])
    assertions.assert_good(slack_user_dm_channel_id['ok'] is True)
    return slack_user_dm_channel_id['channel']['id']


def encode_state(state_params: Dict) -> str:
    state = json.dumps(state_params)

    encoded_state = state.encode()
    base64_encoded_state = base64.urlsafe_b64encode(encoded_state).decode()

    return base64_encoded_state


def decode_state(state: str) -> Dict:
    decoded_state = base64.urlsafe_b64decode(state.encode())
    state_params = json.loads(decoded_state.decode())
    return state_params


def get_fyle_oauth_url(user_id: str, team_id: str) -> str:
    state_params = {
        'user_id': user_id,
        'team_id': team_id
    }

    base64_encoded_state = encode_state(state_params)

    redirect_uri = '{}/fyle/authorization'.format(settings.SLACK_SERVICE_BASE_URL)

    FYLE_OAUTH_URL = '{}/app/developers/#/oauth/authorize?client_id={}&response_type=code&state={}&redirect_uri={}'.format(
        settings.FYLE_ACCOUNTS_URL,
        settings.FYLE_CLIENT_ID,
        base64_encoded_state,
        redirect_uri
    )

    return FYLE_OAUTH_URL


def get_user_display_name(slack_client: WebClient, user_details: Dict) -> str:
    try:
        user_info = slack_client.users_lookupByEmail(email=user_details['email'])
        user_display_name = '<@{}>'.format(user_info['user']['id'])
    except SlackApiError:
        user_display_name = user_details['full_name']

    return user_display_name


def add_message_section_to_ui_block(ui_block: List, section_message: str) -> List[Dict]:
    section = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': section_message
        }
    }
    ui_block.append(section)
    return ui_block
