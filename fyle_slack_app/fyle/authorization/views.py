from django.http.response import HttpResponseRedirect
from django.views import View
from django.conf import settings
from django.utils import timezone

from slack_sdk.web.client import WebClient

from ... import tracking
from ...libs import utils, assertions, http, logger
from ...models import Team, User, ReportPollingDetail
from ...slack.utils import get_slack_user_dm_channel_id, decode_state
from ...slack.ui.authorization.messages import get_post_authorization_message
from ...slack.ui.dashboard import messages as dashboad_messages


logger = logger.get_logger(__name__)


class FyleAuthorization(View):

    FYLE_OAUTH_TOKEN_URL = '{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL)

    def get(self, request):

        error = request.GET.get('error')
        state = request.GET.get('state')

        state_params = decode_state(state)

        # Fetch the slack team
        slack_team = utils.get_or_none(Team, id=state_params['team_id'])
        assertions.assert_found(slack_team, 'slack team not found')

        # Get slack client
        slack_client = WebClient(token=slack_team.bot_access_token)

        # Fetch slack dm channel
        slack_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, state_params['user_id'])

        if error:

            logger.error('Fyle authorization error: {}'.format(error))

            error_message = 'Seems like something went wrong :face_with_head_bandage: \n' \
                        'If the issues still persists, please contact support@fylehq.com'

            # Error when user declines Fyle authorization
            if error == 'access_denied':
                error_message = 'Sad to see you decline us :white_frowning_face: \n' \
                    'Well if you change your mind about us checkout home tab for `Link Your Fyle Account` to link your Fyle account with Slack :zap:'

            slack_client.chat_postMessage(
                    channel=slack_user_dm_channel_id,
                    text=error_message
                )
        else:
            code = request.GET.get('code')

            fyle_refresh_token = self.get_fyle_refresh_token(code)

            user = utils.get_or_none(User, slack_user_id=state_params['user_id'])

            if user is not None:
                # If the user already exists send a message to user indicating they've already linked Fyle account
                self.send_linked_account_message(slack_client, slack_user_dm_channel_id)
            else:
                # Create user
                user = self.create_user(slack_client, slack_team, state_params['user_id'], slack_user_dm_channel_id, fyle_refresh_token)

                self.create_report_polling_entry(user)

                # Send post authorization message to user
                self.send_post_authorization_message(slack_client, slack_user_dm_channel_id)

                # Update user home tab with post auth message
                self.update_user_home_tab_with_post_auth_message(slack_client, state_params['user_id'])

                # Track fyle account link to slack
                self.track_fyle_authorization(user)

        # Redirecting the user to slack bot when auth is complete
        return HttpResponseRedirect('https://slack.com/app_redirect?app={}'.format(settings.SLACK_APP_ID))


    def create_user(self, slack_client, slack_team, user_id, slack_user_dm_channel_id, fyle_refresh_token):

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


    def get_fyle_refresh_token(self, code):
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


    def send_post_authorization_message(self, slack_client, slack_user_dm_channel_id):
        post_authorization_message = get_post_authorization_message()
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            blocks=post_authorization_message
        )


    def send_linked_account_message(self, slack_client, slack_user_dm_channel_id):
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            text='Hey buddy you\'ve already linked your *Fyle* account :rainbow:'
        )


    def update_user_home_tab_with_post_auth_message(self, slack_client, user_id):
        post_authorization_message_view = dashboad_messages.get_post_authorization_message()
        slack_client.views_publish(user_id=user_id, view=post_authorization_message_view)
    

    def create_report_polling_entry(self, user):
        ReportPollingDetail.objects.create(
            user=user,
            last_successful_poll_at=timezone.now()
        )

    def track_fyle_authorization(self, user):
        event_data = {
            'slack_user_id': user.slack_user_id,
            'email': user.email,
            'slack_team_id': user.slack_team.id,
            'slack_team_name': user.slack_team.name
        }

        tracking.identify_user(user.email)

        tracking.track_event(user.email, 'Fyle Account Linked To Slack', event_data)
