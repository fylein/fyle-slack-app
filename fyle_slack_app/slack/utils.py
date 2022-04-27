from typing import Dict
import enum
# pylint: disable=import-error
from forex_python.converter import CurrencyCodes

from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from fyle_slack_app.libs import assertions, http, utils, logger
from fyle_slack_app.models import Team

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
