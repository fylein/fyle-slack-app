from fyle_slack_app.models.users import User
import json

from django.http import JsonResponse, HttpRequest

from fyle_slack_app.slack import SlackView
from fyle_slack_app.slack.events.handlers import SlackEventHandler

from fyle_slack_app.slack.utils import get_slack_client


class SlackEventView(SlackView, SlackEventHandler):

    def post(self, request: HttpRequest) -> JsonResponse:
        slack_payload = json.loads(request.body)

        print('SLACK EVENT -> ', json.dumps(slack_payload, indent=2))

        event_type = slack_payload['type']

        event_response = {}
        # This event is required by slack during our slack event endpoint registering in slack settings
        # When adding endpoint it expects a challenge in response
        # If challenge is not received endpoint is not registered
        if event_type == 'url_verification':
            event_response = {'challenge': slack_payload['challenge']}

        elif event_type == 'event_callback':
            # Events of our interest come under event_callback from slack
            subevent_type = slack_payload['event']['type']
            team_id = slack_payload['team_id']

            if subevent_type == 'file_shared':
                slack_client = get_slack_client(team_id)
                file_id = slack_payload['event']['file_id']

                file_info =  slack_client.files_info(file=file_id)

                user_id = slack_payload['event']['user_id']

                user = User.objects.get(slack_user_id=user_id)

                thread_ts = file_info['file']['shares']['private'][user.slack_dm_channel_id][0]['thread_ts']

                print('THREAD TD -> ', thread_ts)

                a = slack_client.chat_getPermalink(channel=user.slack_dm_channel_id, message_ts=thread_ts)
                pl = a['permalink']

                print('PL -> ', a['permalink'])

                parent_message = slack_client.conversations_history(channel=user.slack_dm_channel_id, latest=thread_ts, inclusive=True, limit=1)

                slack_client.chat_postMessage(text=f'<{pl}|LINK>', channel=user.slack_dm_channel_id)

                for block in parent_message['messages'][0]['blocks']:
                    if block['type'] == 'context':
                        expense_id = block['block_id']
                        break
                print('EXPENSE ID -> ', expense_id)

                return JsonResponse({}, status=200)

            self.handle_event_callback(subevent_type, slack_payload, team_id)

        return JsonResponse(event_response, status=200)
