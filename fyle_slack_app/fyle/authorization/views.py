from django.http import HttpResponseRedirect, HttpRequest
from django.views import View
from django.conf import settings
from django.utils import timezone

from slack_sdk.web.client import WebClient

from fyle_slack_app import tracking
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.models import Team, User, ReportPollingDetail
from fyle_slack_app.slack.utils import get_slack_user_dm_channel_id
from fyle_slack_app.slack.ui.authorization.messages import get_post_authorization_message
from fyle_slack_app.slack.ui.dashboard import messages as dashboard_messages


logger = logger.get_logger(__name__)


class FyleAuthorization(View):

    def get(self, request: HttpRequest) -> HttpResponseRedirect:

        error = request.GET.get('error')
        state = request.GET.get('state')

        state_params = utils.decode_state(state)

        # Fetch the slack team
        slack_team = utils.get_or_none(Team, id=state_params['team_id'])
        assertions.assert_found(slack_team, 'slack team not found')

        # Get slack client
        slack_client = WebClient(token=slack_team.bot_access_token)

        # Fetch slack dm channel
        slack_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, state_params['user_id'])

        if error:

            logger.error('Fyle authorization error: %s', error)

            error_message = 'Seems like something went wrong :face_with_head_bandage: \n' \
                        'If the issues still persists, please contact support@fylehq.com'

            # Error when user declines Fyle authorization
            if error == 'access_denied':
                error_message = 'Sad to see you decline us :white_frowning_face: \n Well if you change your mind about us checkout home tab for `Link Your Fyle Account` to link your Fyle account with Slack :zap:'

            slack_client.chat_postMessage(
                    channel=slack_user_dm_channel_id,
                    text=error_message
                )
        else:
            code = request.GET.get('code')

            user = utils.get_or_none(User, slack_user_id=state_params['user_id'])

            if user is not None:
                # If the user already exists send a message to user indicating they've already linked Fyle account
                self.send_linked_account_message(slack_client, slack_user_dm_channel_id)

            else:

                fyle_refresh_token = fyle_utils.get_fyle_refresh_token(code)

                fyle_profile = fyle_utils.get_fyle_profile(fyle_refresh_token)

                # Create user
                user = self.create_user(slack_client, slack_team, state_params['user_id'], slack_user_dm_channel_id, fyle_refresh_token, fyle_profile['user_id'])

                self.create_report_polling_entry(user)

                # Send post authorization message to user
                self.send_post_authorization_message(slack_client, slack_user_dm_channel_id)

                # Update user home tab with post auth message
                self.update_user_home_tab_with_post_auth_message(slack_client, state_params['user_id'])

                # Track fyle account link to slack
                self.track_fyle_authorization(user)

        # Redirecting the user to slack bot when auth is complete
        return HttpResponseRedirect('https://slack.com/app_redirect?app={}'.format(settings.SLACK_APP_ID))


    # pylint: disable=fixme
    # TODO: Refactor `create_user` this takes in `slack_client` which doesn't define the purpose of this function
    def create_user(self, slack_client: WebClient, slack_team: Team, user_id: str, slack_user_dm_channel_id: str, fyle_refresh_token: str, fyle_user_id: str) -> User:

        # Fetch slack user details
        slack_user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(slack_user_info['ok'] is True)

        # Store slack user in DB
        user = User.objects.create(
            slack_user_id=slack_user_info['user']['id'],
            slack_team=slack_team,
            email=slack_user_info['user']['profile']['email'],
            slack_dm_channel_id=slack_user_dm_channel_id,
            fyle_refresh_token=fyle_refresh_token,
            fyle_user_id=fyle_user_id
        )

        return user


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


    def update_user_home_tab_with_post_auth_message(self, slack_client: WebClient, user_id: str) -> None:
        post_authorization_message_view = dashboard_messages.get_post_authorization_message()
        slack_client.views_publish(user_id=user_id, view=post_authorization_message_view)


    def create_report_polling_entry(self, user: User) -> None:
        ReportPollingDetail.objects.create(
            slack_user=user,
            last_successful_poll_at=timezone.now()
        )


    def track_fyle_authorization(self, user: User) -> None:
        event_data = {
            'asset': 'SLACK_APP',
            'slack_user_id': user.slack_user_id,
            'fyle_user_id': user.fyle_user_id,
            'email': user.email,
            'slack_team_id': user.slack_team.id,
            'slack_team_name': user.slack_team.name
        }

        tracking.identify_user(user.email)

        tracking.track_event(user.email, 'Fyle Account Linked To Slack', event_data)
