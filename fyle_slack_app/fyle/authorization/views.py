import json
import base64

from django.http.response import HttpResponseRedirect
from django.views import View
from django.conf import settings

from slack_sdk.web.client import WebClient

from ...libs import utils, assertions, http
from ...models import Team, User
from ...slack.authorization.tasks import get_slack_user_dm_channel_id
from ...slack.ui.authorization.messages import get_post_authorization_message


class FyleAuthorization(View):

    FYLE_OAUTH_TOKEN_URL = '{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL)

    def get(self, request) -> HttpResponseRedirect:
        code = request.GET.get('code')
        state = request.GET.get('state')

        decoded_state = base64.urlsafe_b64decode(state.encode())
        state_params = json.loads(decoded_state.decode())

        # Fetch the slack team
        slack_team = utils.get_or_none(Team, id=state_params['team_id'])
        assertions.assert_found(slack_team, 'slack team not found')

        # Get slack client
        slack_client = WebClient(token=slack_team.bot_access_token)

        # Fetch slack dm channel
        slack_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, state_params['user_id'])

        fyle_refresh_token = self.get_fyle_refresh_token(code)

        user = utils.get_or_none(User, slack_user_id=state_params['user_id'])

        if user is not None:
            # If the user already exists send a message to user indicating they've already linked Fyle account
            self.send_linked_account_message(slack_client, slack_user_dm_channel_id)
        else:
            # Create user
            user = self.create_user(slack_client, slack_team, state_params['user_id'], slack_user_dm_channel_id, fyle_refresh_token)

            # Send post authorization message to user
            self.send_post_authorization_message(slack_client, slack_user_dm_channel_id)

        # Redirecting the user to slack bot when auth is complete
        return HttpResponseRedirect('https://slack.com/app_redirect?app={}'.format(settings.SLACK_APP_ID))


    def create_user(self, slack_client: WebClient, slack_team: Team, user_id: str, slack_user_dm_channel_id: str, fyle_refresh_token: str) -> User:

        # Fetch slack user details
        slack_user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(slack_user_info['ok'] == True)

        # Store slack user in DB
        user = User.objects.create(
            slack_user_id=slack_user_info['user']['id'],
            slack_team=slack_team,
            email=slack_user_info['user']['profile']['email'],
            slack_dm_channel_id=slack_user_dm_channel_id,
            fyle_refresh_token=fyle_refresh_token
        )

        return user


    def get_fyle_refresh_token(self, code: str) -> str:
        oauth_payload = {
            'grant_type': 'authorization_code',
            'client_id': settings.FYLE_CLIENT_ID,
            'client_secret': settings.FYLE_CLIENT_SECRET,
            'code': code
        }

        oauth_response = http.post(self.FYLE_OAUTH_TOKEN_URL, oauth_payload)
        assertions.assert_good(oauth_response.status_code == 200, 'Error while fetching fyle token details')

        oauth_details = oauth_response.json()

        return oauth_details['refresh_token']


    def send_post_authorization_message(self, slack_client: WebClient, slack_user_dm_channel_id: str) -> None:
        post_authorization_message = get_post_authorization_message()
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            blocks=post_authorization_message
        )


    def send_linked_account_message(self, slack_client: WebClient, slack_user_dm_channel_id: str) -> None:
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            text='Hey buddy you\'ve already linked your *Fyle* account :rainbow:'
        )
