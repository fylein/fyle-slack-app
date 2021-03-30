from slack_sdk.web import WebClient

from django.http import HttpResponse, HttpRequest

from fyle_slack_app.slack import SlackView
from fyle_slack_app.models import Team
from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.slack.commands.handlers import SlackCommandHandler


class SlackCommandView(SlackView, SlackCommandHandler):

    slack_client: WebClient = None

    def _set_slack_client(self, team_id: str) -> None:
        slack_team = utils.get_or_none(Team, id=team_id)
        assertions.assert_found(slack_team, 'Slack team not registered')
        self.slack_client = WebClient(token=slack_team.bot_access_token)


    def post(self, request: HttpRequest, command: str) -> HttpResponse:
        team_id = request.POST['team_id']
        user_id = request.POST['user_id']
        user_dm_channel_id = request.POST['channel_id']

        self._set_slack_client(team_id)

        self.handle_slack_command(command, self.slack_client, user_id, team_id, user_dm_channel_id)

        # Empty "" HttpResponse beacause for slash commands slack return the response as message to user
        return HttpResponse("", status=200)
