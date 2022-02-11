from typing import Dict

from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from fyle_slack_app.libs import assertions, utils
from fyle_slack_app.models import Team
from fyle_slack_app.slack import utils as slack_utils


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


def show_in_progress_confirmation_message(user_id: str, team_id: str, action: str, report_data: dict = None) -> str:
    slack_client = slack_utils.get_slack_client(team_id)
    user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)

    if action == 'unlink_account':
        slack_payload = slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Your request of `Unlink Fyle Account` is being processed :hourglass_flowing_sand:'
        )

        return {
            'message_ts': slack_payload['message']['ts']
        }

    elif action == 'report_approval':
        # Overriding the report approval approve cta text to show as approving
        report_data['message_blocks'][3]['elements'][0]['text']['text'] = 'Approving :hourglass_flowing_sand:'
        report_data['message_blocks'][3]['elements'][0]['value'] = 'pre_auth_message_approve'
        report_data['message_blocks'][3]['elements'][0]['action_id'] = 'pre_auth_message_approve'

        slack_client.chat_update(
            channel=user_dm_channel_id,
            blocks=report_data['message_blocks'],
            ts=report_data['message_ts']
        )
        return {
            "message_blocks": report_data['message_blocks'],
            "message_ts": report_data['message_ts']
        }