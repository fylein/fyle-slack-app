from django.http import HttpResponseRedirect
from django.conf import settings
from django.views import View
from django_q.tasks import async_task

from slack_sdk.web import WebClient

from ...models import Team
from ...libs import utils, assertions, logger
from .tasks import get_slack_user_dm_channel_id
from ... import tracking


logger = logger.get_logger(__name__)


class SlackAuthorization(View):

    def get(self, request):

        error = request.GET.get('error')

        # If any error occured redirecting to FyleHQ website
        if error:

            logger.error('Slack bot installation failed {}'.format(error))

            return HttpResponseRedirect('https://www.fylehq.com/')

        code = request.GET.get('code')

        # An empty string is a valid token for this request
        slack_client = WebClient('')

        auth_response = slack_client.oauth_v2_access(
            client_id=settings.SLACK_CLIENT_ID,
            client_secret=settings.SLACK_CLIENT_SECRET,
            code=code
        )

        assertions.assert_auth(auth_response['ok'] is True)

        user_id = auth_response['authed_user']['id']
        team_id = auth_response['team']['id']
        team_name = auth_response['team']['name']
        bot_user_id = auth_response['bot_user_id']
        bot_access_token = auth_response['access_token']

        slack_team = utils.get_or_none(Team, id=team_id)

        if slack_team is not None:
            # If slack team already exists means
            # Slack bot is already installed in the workspace
            # Send user a message that bot is already installed
            slack_client = WebClient(token=bot_access_token)
            slack_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)

            self.send_bot_already_installed_message(slack_client, slack_user_dm_channel_id)

        else:

            slack_team = Team.objects.create(
                id=team_id,
                name=team_name,
                bot_user_id=bot_user_id,
                bot_access_token=bot_access_token
            )

            # Background task to broadcast pre auth message to all slack workspace members
            async_task('fyle_slack_app.slack.authorization.tasks.broadcast_installation_message', team_id)

            slack_client = WebClient(token=bot_access_token)

            # Tracking slack bot installation to Mixpanel
            self.track_installation(user_id, slack_team, slack_client)

        return HttpResponseRedirect('https://slack.com/app_redirect?app={}'.format(settings.SLACK_APP_ID))


    def send_bot_already_installed_message(self, slack_client, slack_user_dm_channel_id):
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            text='Hey buddy, Fyle app has already been installed on your workspace :rainbow:'
        )


    def track_installation(self, user_id, slack_team, slack_client):
        user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(user_info['ok'] == True)

        user_email = user_info['user']['profile']['email']

        tracking.identify_user(user_email)

        event_data = {
            'slack_user_id': user_id,
            'slack_team_id': slack_team.id,
            'slack_team_name': slack_team.name,
            'installer_email': user_email,
            'installer_name': user_info['user']['real_name'],
            'is_slack_admin': user_info['user']['is_admin']
        }

        tracking.track_event(user_email, 'Slack Bot Installed', event_data)