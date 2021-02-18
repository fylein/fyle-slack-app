from slack_sdk import WebClient

from ...libs import utils, assertions
from ...models import Team
from ..ui.authorization import messages
from ...slack.utils import get_slack_user_dm_channel_id, get_fyle_oauth_url


def broadcast_installation_message(slack_team_id: str) -> None:
    slack_team = utils.get_or_none(Team, id=slack_team_id)
    assertions.assert_found(slack_team, 'slack team is not registered')

    slack_client = WebClient(token=slack_team.bot_access_token)

    slack_workspace_users = slack_client.users_list()
    assertions.assert_good(slack_workspace_users['ok'] == True)

    for workspace_user in slack_workspace_users['members']:
        if workspace_user['deleted'] == False and workspace_user['is_bot'] == False:

            fyle_oauth_url = get_fyle_oauth_url(workspace_user['id'], workspace_user['team_id'])

            workspace_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, workspace_user['id'])
            
            pre_auth_message = messages.get_pre_authorization_message(workspace_user['real_name'], fyle_oauth_url)
            
            slack_client.chat_postMessage(
                channel=workspace_user_dm_channel_id,
                blocks=pre_auth_message
            )
