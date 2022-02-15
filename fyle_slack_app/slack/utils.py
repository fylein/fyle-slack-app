from typing import Dict
from enum import Enum

from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from fyle_slack_app.libs import assertions, utils
from fyle_slack_app.models import Team


class async_operation_message(Enum):
    unlink_account = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': 'Your request of `Unlink Fyle Account` is being processed :hourglass_flowing_sand:'
        }
    }
    
    approve_report = {
        'type': 'button',
        'style': 'primary',
        'text': {
            'type': 'plain_text',
            'text': 'Approving :hourglass_flowing_sand:',
            'emoji': True
        },
        'action_id': 'pre_auth_message_approve',
        'value': 'pre_auth_message_approve',
    }


def get_slack_user_dm_channel_id(slack_client: WebClient, user_id: str) -> str:
    slack_user_dm_channel_id = slack_client.conversations_open(users=[user_id])
    assertions.assert_good(slack_user_dm_channel_id['ok'] is True)
    return slack_user_dm_channel_id['channel']['id']


def get_slack_client(team_id: str) -> WebClient:
    slack_team = utils.get_or_none(Team, id=team_id)
    assertions.assert_found(slack_team, 'Slack team not registered')
    return WebClient(token=slack_team.bot_access_token)


def get_user_display_name(slack_client: WebClient, user_details: Dict) -> str:
    try:
        user_info = slack_client.users_lookupByEmail(email=user_details['email'])
        user_display_name = '<@{}>'.format(user_info['user']['id'])
    except SlackApiError:
        user_display_name = user_details['full_name']

    return user_display_name

