from django.http import HttpResponse, HttpRequest

from fyle_slack_app.slack import SlackView
from fyle_slack_app.slack.commands.handlers import SlackCommandHandler


class SlackCommandView(SlackView, SlackCommandHandler):

    def post(self, request: HttpRequest, command: str) -> HttpResponse:
        team_id = request.POST['team_id']
        user_id = request.POST['user_id']
        user_dm_channel_id = request.POST['channel_id']
        trigger_id = request.POST['trigger_id']

        print('REQIEST -> ', request.POST)

        self.handle_slack_command(command, user_id, team_id, user_dm_channel_id, trigger_id)

        # Empty "" HttpResponse beacause for slash commands slack return the response as message to user
        return HttpResponse("", status=200)
