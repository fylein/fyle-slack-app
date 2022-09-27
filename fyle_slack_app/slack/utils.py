from typing import List, Dict, Union
import enum
# pylint: disable=import-error

from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from babel.numbers import get_currency_precision, get_currency_symbol

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

def get_file_content_from_slack(url: str, bot_access_token: str) -> str:
    headers = {
        'Authorization': 'Bearer {}'.format(bot_access_token)
    }
    file = http.get(url, headers=headers)
    return file.content


def round_amount(amount: float, currency: str) -> float:
    """
    `round_amount(10.5678, 'USD') -> 10.57`

    `round_amount(10.5678, 'OMR') -> 10.568`

    `round_amount(10.5678, 'JPY') -> 11`

    `round_amount(10.5678, 'CLF') -> 10.5678`

    - Rounds the amount given to the appropriate number of decimal digits as specfied in the iso4217 standard.
    - Throws `ValueError` if amount or currency is `None`

    More info about iso4217 international standard for currencies - https://en.wikipedia.org/wiki/ISO_4217
    """

    if amount is None and currency is None:
        raise ValueError('Error while rounding amount: Amount and Currency is None!')

    if amount is None:
        raise ValueError('Error while rounding amount: Amount is None!')

    if currency is None:
        raise ValueError('Error while rounding amount: Currency is None!')

    # If given a currency that we could not find precision for, this function returns 2 as a default
    precision = get_currency_precision(currency)

    # Round fails for cases like 2.665 and 2.675 both returns 2.67 so adding the 1e-9 helps in handling the precision issues
    # link https://docs.python.org/3/tutorial/floatingpoint.html#tut-fp-issues
    rounded_amount = round(amount + 1e-9, precision)

    return rounded_amount

def format_currency(currency: str) -> str:
    """
    `format_currency('USD') -> '$'`

    `format_currency('OMR') -> 'OMR '`

    - Returns a formatted representation of a currency code following iso4217, to be used only for representational purposes with amount.
    - If given a currency code for which a symbol is found, returns that symbol as is.
    - If given a currency code for which a symbol is not found, returns the code with a space appended for better readability.
    - Throws `ValueError` if currency is `None`

    More info about iso4217 international standard for currencies - https://en.wikipedia.org/wiki/ISO_4217
    """
    if currency is None:
        raise ValueError('Error while formatting currency: Currency is None!')

    # If the currency doesn't have any symbol, the currency code is returned
    currency_symbol = get_currency_symbol(currency)
    is_currency_having_symbol = currency != currency_symbol

    # Add a space to the currency, if it the currency doesn't have any symbol
    # Example, if currency is OMR, for amount 100 this will end up displaying OMR 100 instead of OMR100
    formatted_currency = currency_symbol if is_currency_having_symbol else currency_symbol + ' '
    return formatted_currency


def get_display_amount(amount: Union[str, int, float], currency: str) -> str:
    """
    `get_display_amount(10.56, 'USD') -> '$10.56'`

    `get_display_amount(10.56, 'OMR') -> 'OMR 10.560'`

    `get_display_amount(10.56, 'ISK') -> 'kr11'`

    `get_display_amount(10.56, 'CLF') -> 'CLF 10.5600'`

    - Formats the amount given to the appropriate number of decimal digits as specfied in the iso4217 standard.
    - Prepends a formatted representation of the currency code given to the amount.
    - This function can handle negative amount.
    - Throws `ValueError` if amount is `None` or is invalid.
    - Throws `ValueError` if currency is `None`

    More info about iso4217 international standard for currencies - https://en.wikipedia.org/wiki/ISO_4217
    """

    if amount is None:
        raise ValueError('Error while formatting amount: Amount is None!')

    # Convert and clean the amount, if it is a string
    if isinstance(amount, str):
        # An amount with '.' as the decimal separator and ',' as the thousand separator is expected for conversion to work properly
        cleaned_amount = amount.replace(',', '')
        amount = float(cleaned_amount)

    # Sign to add at the beginning
    sign = '-' if amount < 0 else ''
    amount = abs(amount)

    # Gets the currency precision and symbol for currency specified
    formatted_currency = format_currency(currency)
    currency_precision = get_currency_precision(currency)

    # Create a format string and round the amount to currency precision
    format_string = '{:,.' + str(currency_precision) + 'f}'

    # Format fails for cases like 2.665 and 2.675 both returns 2.67 so adding the 1e-9 helps in handling the precision issues
    # link https://docs.python.org/3/tutorial/floatingpoint.html#tut-fp-issues
    formatted_amount = format_string.format(amount + 1e-9)
    formatted_amount = f'{formatted_currency}{formatted_amount}'

    # Finally, add the sign back to the formatted amount and return the result
    formatted_amount = f'{sign}{formatted_amount}'

    return formatted_amount

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
