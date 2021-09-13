import json
from os import lchown

from django.http import HttpRequest, JsonResponse

from fyle_slack_app.slack import SlackView
from fyle_slack_app.slack.interactives.block_action_handlers import BlockActionHandler
from fyle_slack_app.slack.interactives.shortcut_handlers import ShortcutHandler
from fyle_slack_app.slack.interactives.view_submission_handlers import ViewSubmissionHandler


class SlackInteractiveView(SlackView, BlockActionHandler, ShortcutHandler, ViewSubmissionHandler):

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
            return self.handle_block_actions(slack_payload, user_id, team_id)

        elif event_type == 'shortcut':
            # Call handler function from ShortcutHandler
            return self.handle_shortcuts(slack_payload, user_id, team_id)

        elif event_type == 'view_submission':
            # Call handler function from ViewSubmissionHandler
            return self.handle_view_submission(slack_payload, user_id, team_id)

        elif event_type == 'block_suggestion':
            # Call handler function from BlockActionHandler
            value = slack_payload['value']
            categories = [
                {
                    'text': {
                        'type': 'plain_text',
                        'text': 'Custom Field Category',
                        'emoji': True,
                    },
                    'value': '136250',
                },
                {
                    'text': {
                        'type': 'plain_text',
                        'text': 'Internet',
                        'emoji': True,
                    },
                    'value': '136518',
                },
                {
                    'text': {
                        'type': 'plain_text',
                        'text': 'Office Supplies',
                        'emoji': True,
                    },
                    'value': '1234',
                },
                {
                    'text': {
                        'type': 'plain_text',
                        'text': 'Stuff for office',
                        'emoji': True,
                    },
                    'value': '1234',
                },
            ]

            options = []
            for category in categories:
                if value.lower() in category['text']['text'].lower():
                    options.append(category)

            return JsonResponse({'options': options})

        return JsonResponse({}, status=200)
