from slack_sdk import WebClient

from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.models import Team
from fyle_slack_app.slack.ui.authorization import messages
from fyle_slack_app.slack.utils import get_slack_user_dm_channel_id


def broadcast_installation_message(slack_team_id: str) -> None:
    slack_team = utils.get_or_none(Team, id=slack_team_id)
    assertions.assert_found(slack_team, 'slack team is not registered')

    slack_client = WebClient(token=slack_team.bot_access_token)

    slack_workspace_users = slack_client.users_list()
    assertions.assert_good(slack_workspace_users['ok'] is True)

    for workspace_user in slack_workspace_users['members']:
        if workspace_user['deleted'] is False and workspace_user['is_bot'] is False:

            fyle_oauth_url = fyle_utils.get_fyle_oauth_url(workspace_user['id'], workspace_user['team_id'])

            workspace_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, workspace_user['id'])

            pre_auth_message = messages.get_pre_authorization_message(workspace_user['real_name'], fyle_oauth_url)

            slack_client.chat_postMessage(
                channel=workspace_user_dm_channel_id,
                blocks=pre_auth_message
            )
