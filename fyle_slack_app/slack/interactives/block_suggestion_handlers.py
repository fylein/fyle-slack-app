from typing import Dict, List

from django.http import JsonResponse

from fyle_slack_app.models.users import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.libs import logger, utils
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.interactives.tasks import check_project_in_form


logger = logger.get_logger(__name__)


class BlockSuggestionHandler:

    _block_suggestion_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_block_suggestion_handlers(self):
        self._block_suggestion_handlers = {
            'category_id': self.handle_category_suggestion,
            'project_id': self.handle_project_suggestion,
            'cost_center_id': self.handle_cost_center_suggestion,
            'currency': self.handle_currency_suggestion
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

        user = utils.get_or_none(User, slack_user_id=user_id)
        category_value_entered = slack_payload['value']

        fyle_expense = FyleExpense(user)

        category_query_params = {
            'offset': 0,
            'limit': '30',
            'order': 'display_name.asc',
            'display_name': 'ilike.%{}%'.format(category_value_entered),
            'system_category': 'not_in.(Unspecified, Per Diem, Mileage, Activity)',
            'is_enabled': 'eq.{}'.format(True)
        }

        private_metadata = slack_payload['view']['private_metadata']

        decoded_private_metadata = utils.decode_state(private_metadata)

        form_current_state = slack_payload['view']['state']['values']

        is_project_available, project = check_project_in_form(form_current_state, decoded_private_metadata)

        if is_project_available is True:
            category_query_params['id'] = 'in.{}'.format(tuple(project['data'][0]['category_ids']))

        suggested_categories = fyle_expense.get_categories(category_query_params)

        category_options = []
        if suggested_categories['count'] > 0:
            for category in suggested_categories['data']:

                category_display_name = category['display_name']
                if category['name'] == category['sub_category']:
                    category_display_name = category['name']

                option = {
                    'text': {
                        'type': 'plain_text',
                        'text': category_display_name,
                        'emoji': True,
                    },
                    'value': str(category['id']),
                }
                category_options.append(option)

        return category_options


    def handle_currency_suggestion(self, slack_payload: Dict, user_id: str, team_id: str) -> List:

        currencies = FyleExpense.get_currencies()

        currency_value_entered = slack_payload['value']

        currency_options = []
        for currency in currencies:
            if currency.startswith(currency_value_entered.upper()):
                option = {
                    'text': {
                        'type': 'plain_text',
                        'text': currency,
                        'emoji': True,
                    },
                    'value': currency,
                }
                currency_options.append(option)

        return currency_options


    def handle_project_suggestion(self, slack_payload: Dict, user_id: str, team_id: str) -> List:

        user = utils.get_or_none(User, slack_user_id=user_id)
        project_value_entered = slack_payload['value']
        query_params = {
            'offset': 0,
            'limit': '10',
            'order': 'display_name.asc',
            'display_name': 'ilike.%{}%'.format(project_value_entered),
            'is_enabled': 'eq.{}'.format(True)
        }

        fyle_expense = FyleExpense(user)
        suggested_projects = fyle_expense.get_projects(query_params)

        project_options = []
        if suggested_projects['count'] > 0:
            for project in suggested_projects['data']:

                project_display_name = project['display_name']
                if project['name'] == project['sub_project']:
                    project_display_name = project['name']

                option = {
                    'text': {
                        'type': 'plain_text',
                        'text': project_display_name,
                        'emoji': True,
                    },
                    'value': str(project['id']),
                }
                project_options.append(option)

        return project_options


    def handle_cost_center_suggestion(self, slack_payload: Dict, user_id: str, team_id: str) -> List:

        user = utils.get_or_none(User, slack_user_id=user_id)
        cost_center_value_entered = slack_payload['value']
        query_params = {
            'offset': 0,
            'limit': '10',
            'order': 'name.asc',
            'name': 'ilike.%{}%'.format(cost_center_value_entered),
            'is_enabled': 'eq.{}'.format(True)
        }

        fyle_expense = FyleExpense(user)
        suggested_cost_centers = fyle_expense.get_cost_centers(query_params)

        cost_center_options = []
        if suggested_cost_centers['count'] > 0:
            for cost_center in suggested_cost_centers['data']:
                option = {
                    'text': {
                        'type': 'plain_text',
                        'text': cost_center['name'],
                        'emoji': True,
                    },
                    'value': str(cost_center['id']),
                }
                cost_center_options.append(option)

        return cost_center_options
