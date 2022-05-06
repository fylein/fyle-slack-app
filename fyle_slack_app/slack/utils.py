from typing import List, Dict
import enum
# pylint: disable=import-error
from forex_python.converter import CurrencyCodes

from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from fyle_slack_app.libs import assertions, http, utils, logger
from fyle_slack_app.models import Team, User

logger = logger.get_logger(__name__)


class AsyncOperation(enum.Enum):
    UNLINKING_ACCOUNT = 'UNLINKING_ACCOUNT'
    APPROVING_REPORT = 'APPROVING_REPORT'


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


def get_currency_symbol(currency: str) -> str:
    c = CurrencyCodes()

    try:
        curr = c.get_symbol(currency)
    except ValueError as error:
        logger.error('Error fetching currency symbol of currency = %s', currency)
        logger.error('Error -> %s', error)

    symbol = curr if curr is not None else currency

    return symbol


def get_file_content_from_slack(url: str, bot_access_token: str) -> str:
    headers = {
        'Authorization': 'Bearer {}'.format(bot_access_token)
    }
    file = http.get(url, headers=headers)
    return file.content


def get_slack_latest_parent_message(user: User, slack_client: WebClient, thread_ts: str) -> Dict:
    message_history = slack_client.conversations_history(channel=user.slack_dm_channel_id, latest=thread_ts, inclusive=True, limit=1)
    parent_message = message_history['messages'][0] if message_history['messages'] and message_history['messages'][0] else {}
    return parent_message


def send_slack_response_in_thread(user: User, slack_client: WebClient, thread_message_block: List[Dict], thread_ts: str) -> Dict:
    response = slack_client.chat_postMessage(
        channel=user.slack_dm_channel_id,
        blocks=thread_message_block,
        thread_ts=thread_ts
    )
    return response


def update_slack_parent_message(user: User, slack_client: WebClient, parent_message: Dict, response_block: List[Dict], hide_only_primary_button: bool, hide_all_buttons: bool):
    parent_message_blocks = parent_message['blocks']
    parent_message_ts = parent_message['ts']

    if hide_only_primary_button:
        if parent_message_blocks[-1] and 'elements' in parent_message_blocks[-1] and len(parent_message_blocks[-1]['elements']) > 1:
            del parent_message_blocks[-1]['elements'][0]

    elif hide_all_buttons:
        if parent_message_blocks[-1] and 'elements' in parent_message_blocks[-1]:
            parent_message_blocks[-1] = response_block[0]

    slack_client.chat_update(
        blocks=parent_message_blocks,
        ts=parent_message_ts,
        channel=user.slack_dm_channel_id
    )
