import json

from typing import Dict, List

from django.http import JsonResponse

from fyle_slack_app.models.users import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.libs import logger, utils
from fyle_slack_app.slack import utils as slack_utils


logger = logger.get_logger(__name__)


class BlockSuggestionHandler:

    _block_suggestion_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_block_suggestion_handlers(self):
        self._block_suggestion_handlers = {
            'category': self.handle_category_suggestion
        }


    # Gets called when function with an action is not found
    def _handle_invalid_block_suggestions(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        slack_client = slack_utils.get_slack_client(team_id)

        user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Looks like something went wrong :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the block_suggestions from slack
    def handle_block_suggestions(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        '''
            Check if any function is associated with the action
            If present handler will call the respective function
            If not present call `handle_invalid_block_suggestions` to send a prompt to user
        '''

        # Initialize handlers
        self._initialize_block_suggestion_handlers()

        action_id = slack_payload['action_id']

        handler = self._block_suggestion_handlers.get(action_id, self._handle_invalid_block_suggestions)

        options = handler(slack_payload, user_id, team_id)

        return JsonResponse({'options': options})


    def handle_category_suggestion(self, slack_payload: Dict, user_id: str, team_id: str) -> List:
        print('SLACK PAYLOAD -> ', json.dumps(slack_payload, indent=2))
        user = utils.get_or_none(User, slack_user_id=user_id)
        category_value_entered = slack_payload['value']
        query_params = {
            'offset': 0,
            'limit': '20',
            'order': 'display_name.asc',
            'display_name': 'ilike.%{}%'.format(category_value_entered),
            'is_enabled': 'eq.{}'.format(True)
        }
        suggested_categories = FyleExpense.get_categories(user, query_params)

        category_options = []
        if suggested_categories['count'] > 0:
            for category in suggested_categories['data']:
                option = {
                    'text': {
                        'type': 'plain_text',
                        'text': category['display_name'],
                        'emoji': True,
                    },
                    'value': str(category['id']),
                }
                category_options.append(option)

        return category_options
