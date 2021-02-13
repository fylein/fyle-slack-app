from django.http import HttpResponseRedirect
from django.conf import settings
from django.views import View
from django_q.tasks import async_task

from slack_sdk.web import WebClient

from ...models import SlackTeam
from ...libs import utils, assertions


class SlackAuthorization(View):

    def get(self, request) -> HttpResponseRedirect:

        error = request.GET.get('error')

        # If any error occured redirecting to FyleHQ website
        if error:
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

        team_id = auth_response['team']['id']
        team_name = auth_response['team']['name']
        bot_user_id = auth_response['bot_user_id']
        bot_access_token = auth_response['access_token']

        slack_team = utils.get_or_none(SlackTeam, id=team_id)

        assertions.assert_valid(slack_team is None, 'Fyle app has already been installed on your workspace')

        slack_team = SlackTeam.objects.create(
            id=team_id,
            name=team_name,
            bot_user_id=bot_user_id,
            bot_access_token=bot_access_token
        )

        # Background task to broadcast pre auth message to all slack workspace members
        async_task('fyle_slack_app.slack.authorization.tasks.broadcast_installation_message', team_id)

        return HttpResponseRedirect('https://slack.com/app_redirect?app={}'.format(settings.SLACK_APP_ID))
