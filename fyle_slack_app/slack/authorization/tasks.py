import json
import base64

from slack_sdk import WebClient
from django.conf import settings

from ...libs import utils, assertions
from ...models import Team
from ..ui.authorization import messages


def get_slack_user_dm_channel_id(slack_client: WebClient, user_id: str) -> str:
    slack_user_dm_channel_id = slack_client.conversations_open(users=[user_id])
    assertions.assert_good(slack_user_dm_channel_id['ok'] == True)
    return slack_user_dm_channel_id['channel']['id']


def get_fyle_oauth_url(user_id: str, team_id: str) -> str:
    state_params = {
        'user_id': user_id,
        'team_id': team_id
    }
    state = json.dumps(state_params)

    encoded_state = state.encode()
    base64_encoded_state = base64.urlsafe_b64encode(encoded_state).decode()

    redirect_uri = '{}/fyle/authorization'.format(settings.SLACK_SERVICE_BASE_URL)

    FYLE_OAUTH_URL = '{}/app/developers/#/oauth/authorize?client_id={}&response_type=code&state={}&redirect_uri={}'.format(
        settings.FYLE_ACCOUNTS_URL,
        settings.FYLE_CLIENT_ID,
        base64_encoded_state,
        redirect_uri
    )

    return FYLE_OAUTH_URL

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
