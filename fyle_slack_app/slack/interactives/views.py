import json

from django.http import HttpRequest, JsonResponse

from fyle_slack_app.slack import SlackView
from fyle_slack_app.slack.interactives.block_action_handlers import BlockActionHandler
from fyle_slack_app.slack.interactives.shortcut_handlers import ShortcutHandler
from fyle_slack_app.slack.interactives.view_submission_handlers import ViewSubmissionHandler


class SlackInteractiveView(SlackView):

    def post(self, request: HttpRequest) -> JsonResponse:
        payload = request.POST.get('payload')
        slack_payload = json.loads(payload)

        # Extract details from payload
        user_id = slack_payload['user']['id']
        team_id = slack_payload['team']['id']

        event_type = slack_payload['type']

        # Check interactive event type and call it's respective handler
        if event_type == 'block_actions':
            # Call handler function from BlockActionHandler
            return BlockActionHandler().handle_block_actions(slack_payload, user_id, team_id)

        elif event_type == 'shortcut':
            # Call handler function from ShortcutHandler
            return ShortcutHandler().handle_shortcuts(slack_payload, user_id, team_id)

        elif event_type == 'view_submission':
            # Call handler function from ViewSubmissionHandler
            return ViewSubmissionHandler().handle_view_submission(slack_payload, user_id, team_id)

        return JsonResponse({}, status=200)
