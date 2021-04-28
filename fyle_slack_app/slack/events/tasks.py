from slack_sdk import WebClient

from fyle_slack_app.fyle.utils import get_fyle_oauth_url
from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.models import Team, User
from fyle_slack_app.slack.utils import get_slack_user_dm_channel_id
from fyle_slack_app.slack.ui.authorization import messages


def new_user_joined_pre_auth_message(user_id: str, team_id: str) -> None:
    # Check if the user has already authorized Fyle account
    # If already authorized, no need to send pre auth message
    user = utils.get_or_none(User, slack_user_id=user_id)

    if user is None:
        team = utils.get_or_none(Team, id=team_id)
        assertions.assert_found(team, 'Slack team not registered')

        slack_client = WebClient(token=team.bot_access_token)

        user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(user_info['ok'] is True)

        user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)

        fyle_oauth_url = get_fyle_oauth_url(user_id, team_id)

        pre_auth_message = messages.get_pre_authorization_message(user_info['user']['real_name'], fyle_oauth_url)

        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            blocks=pre_auth_message
        )


def uninstall_app(team_id: str) -> None:
    team = utils.get_or_none(Team, id=team_id)

    if team is not None:
        # Deleting team :)
        team.delete()
