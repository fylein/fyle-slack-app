import json
import base64

from django.http.response import JsonResponse
from django.views import View
from django.conf import settings

from slack_sdk.web.client import WebClient

from ...libs import utils, assertions, http
from ...models import SlackTeam, FyleEmployee, SlackUser, SlackFyleUserMapping
from ...slack import get_slack_client
from ...slack.authorization.tasks import get_slack_user_dm_channel_id
from ...slack.ui.authorization.messages import get_post_authorization_message


class FyleAuthorization(View):

    FYLE_OAUTH_TOKEN_URL = '{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL)
    FYLE_MY_PROFILE_URL = 'https://platform.fyle.tech/fyler/my_profile'

    def get(self, request) -> JsonResponse:
        code = request.GET.get('code')
        state = request.GET.get('state')

        decoded_state = base64.urlsafe_b64decode(state.encode())
        state_params = json.loads(decoded_state.decode())

        # Fetch the slack team
        slack_team = utils.get_or_none(SlackTeam, id=state_params['team_id'])
        assertions.assert_found(slack_team, 'slack team not found')

        # Get slack client
        slack_client = get_slack_client(slack_team.bot_access_token)

        # Fetch slack dm channel
        slack_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, state_params['user_id'])

        # Create slack user
        slack_user = self.create_slack_user(slack_client, slack_team, state_params['user_id'], slack_user_dm_channel_id)

        # Create fyle employee
        fyle_employee = self.create_fyle_employee(code)

        # Create slack fyle user mapping
        slack_fyle_user_mapping = self.create_slack_fyle_user_mapping(slack_user, fyle_employee)

        # Send post authorization message to user
        self.send_post_authorization_message(slack_client, slack_user_dm_channel_id)

        return JsonResponse({}, status=200)


    def create_slack_user(self, slack_client: WebClient, slack_team: SlackTeam, user_id: str, slack_user_dm_channel_id: str) -> SlackUser:

        # Fetch slack user details
        slack_user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(slack_user_info['ok'] == True)

        # Store slack user in DB
        slack_user = SlackUser.objects.create(
            id=slack_user_info['user']['id'],
            slack_team_id=slack_team,
            email=slack_user_info['user']['profile']['email'],
            dm_channel_id=slack_user_dm_channel_id
        )

        return slack_user


    def create_slack_fyle_user_mapping(self, slack_user: SlackUser, fyle_employee: FyleEmployee) -> SlackFyleUserMapping:
        slack_fyle_user_mapping = SlackFyleUserMapping.objects.create(
            slack_user_id=slack_user,
            fyle_employee_id=fyle_employee
        )

        return slack_fyle_user_mapping


    def create_fyle_employee(self, code: str) -> FyleEmployee:
        oauth_payload = {
        'grant_type': 'authorization_code',
        'client_id': settings.FYLE_CLIENT_ID,
        'client_secret': settings.FYLE_CLIENT_SECRET,
        'code': code
        }

        oauth_response = http.post(self.FYLE_OAUTH_TOKEN_URL, oauth_payload)
        assertions.assert_good(oauth_response.status_code == 200, 'Error while fetching fyle token details')

        oauth_response = oauth_response.json()

        refresh_token = oauth_response['refresh_token']
        access_token = oauth_response['access_token']

        headers = {
            'X-AUTH-TOKEN': access_token
        }
        my_profile_response = http.get(self.FYLE_MY_PROFILE_URL, headers=headers)
        assertions.assert_good(my_profile_response.status_code == 200, 'Error while fetching fyle profile details')

        my_profile_response = my_profile_response.json()['data']

        fyle_employee = FyleEmployee.objects.create(
            id=my_profile_response['id'],
            refresh_token=refresh_token,
            email=my_profile_response['user']['email'],
            org_id=my_profile_response['org_id'],
            org_name=my_profile_response['org']['name'],
            org_currency=my_profile_response['org']['currency']
        )

        return fyle_employee


    def send_post_authorization_message(self, slack_client: WebClient, slack_user_dm_channel_id: str) -> None:
        post_authorization_message = get_post_authorization_message()
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            blocks=post_authorization_message
        )
