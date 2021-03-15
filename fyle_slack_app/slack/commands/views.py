from slack_sdk.web import WebClient

from django.http.response import HttpResponse

from ...slack import SlackView
from ...models import Team
from ...libs import utils, assertions
from .handlers import SlackCommandHandler


class SlackCommandView(SlackView, SlackCommandHandler):

    slack_client = None

    def _set_slack_client(self, team_id) -> None:
        slack_team = utils.get_or_none(Team, id=team_id)
        assertions.assert_found(slack_team, 'Slack team not registered')
        self.slack_client = WebClient(token=slack_team.bot_access_token)


    def post(self, request, command):
        team_id = request.POST['team_id']
        user_id = request.POST['user_id']
        user_dm_channel_id = request.POST['channel_id']

        self._set_slack_client(team_id)

        self.handle_slack_command(command, self.slack_client, user_id, team_id, user_dm_channel_id)

        # Empty "" HttpResponse beacause for slash commands slack return the response as message to user
        return HttpResponse("", status=200)
