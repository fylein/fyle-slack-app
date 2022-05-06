import datetime
import json

from typing import Callable, Dict, Union
from dateutil.parser import parse

from django.http.response import JsonResponse
from django.core.cache import cache

from django_q.tasks import async_task

from django_q.tasks import async_task

from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.models import User
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.libs import utils
from fyle_slack_app.slack.ui.expenses import messages as expense_messages
from fyle_slack_app.slack.interactives.block_action_handlers import BlockActionHandler




class ViewSubmissionHandler:

    _view_submission_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_view_submission_handlers(self):
        self._view_submission_handlers = {
            'upsert_expense': self.handle_upsert_expense,
            'submit_report': self.handle_submit_report,
            'add_expense_to_report': self.handle_add_expense_to_report,
            'feedback_submission': self.handle_feedback_submission,
            'report_approval_from_modal': self.handle_report_approval_from_modal
        }


    # Gets called when function with a callback id is not found
    def _handle_invalid_view_submission(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        slack_client = slack_utils.get_slack_client(team_id)

        user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Looks like something went wrong :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the view_submission from slack
    def handle_view_submission(self, slack_payload: Dict, user_id: str, team_id: str) -> Callable:
        '''
            Check if any function is associated with the action
            If present handler will call the respective function
            If not present call `handle_invalid_view_submission` to send a prompt to user
        '''

        # Initialize handlers
        self._initialize_view_submission_handlers()

        callback_id = slack_payload['view']['callback_id']

        handler = self._view_submission_handlers.get(callback_id, self._handle_invalid_view_submission)

        return handler(slack_payload, user_id, team_id)


    def handle_upsert_expense(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        user = utils.get_or_none(User, slack_user_id=user_id)

        form_values = slack_payload['view']['state']['values']

        expense_payload, validation_errors = self.extract_form_values_and_validate(user, form_values)
        cache_key = '{}.form_metadata'.format(slack_payload['view']['id'])
        form_metadata = cache.get(cache_key)

        expense_payload['source'] = 'SLACK'
        expense_payload['spent_at'] = parse(expense_payload['spent_at']).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        print('EXPENSE -> ', json.dumps(expense_payload, indent=2))

        expense_id = form_metadata.get('expense_id')
        message_ts = form_metadata.get('message_ts')

        # If valdiation errors are present then return errors
        if bool(validation_errors) is True:
            return JsonResponse({
                'response_action': 'errors',
                'errors': validation_errors
            })

        async_task(
            'fyle_slack_app.slack.interactives.tasks.handle_upsert_expense',
            user,
            slack_payload['view']['id'],
            team_id,
            expense_payload,
            expense_id,
            message_ts
        )

        return JsonResponse({})


    def handle_submit_report(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:

        user = utils.get_or_none(User, slack_user_id=user_id)

        report_id = slack_payload['view']['private_metadata']

        fyle_expense = FyleExpense(user)

        report_query_params = {
            'offset': 0,
            'limit': '1',
            'order': 'created_at.desc',
            'id': 'eq.{}'.format(report_id)
        }

        report = fyle_expense.get_reports(query_params=report_query_params)

        slack_client = slack_utils.get_slack_client(team_id)

        report_submitted_message = expense_messages.report_submitted_message(user, report['data'][0])

        slack_client.chat_postMessage(channel=user.slack_dm_channel_id, blocks=report_submitted_message)

        return JsonResponse({})


    def handle_add_expense_to_report(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:

        add_expense_to_report_form_values = slack_payload['view']['state']['values']
        expense_id = slack_payload['view']['private_metadata']

        if 'TEXT_add_to_new_report_block' in add_expense_to_report_form_values:
            report_name = add_expense_to_report_form_values['TEXT_add_to_new_report_block']['report_name']['value']

        elif 'SELECT_add_to_existing_report_block' in add_expense_to_report_form_values:
            existing_report_id = add_expense_to_report_form_values['SELECT_add_to_existing_report_block']['existing_report']['selected_option']['value']

        encoded_private_metadata = slack_payload['view']['private_metadata']
        private_metadata = utils.decode_state(encoded_private_metadata)

    def handle_feedback_submission(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        user = utils.get_or_none(User, slack_user_id=user_id)
        form_values = slack_payload['view']['state']['values']
        encoded_private_metadata = slack_payload['view']['private_metadata']
        private_metadata = utils.decode_state(encoded_private_metadata)

        async_task(
            'fyle_slack_app.slack.interactives.tasks.handle_feedback_submission',
            user,
            team_id,
            form_values,
            private_metadata
        )

        return JsonResponse({})


    def extract_form_values_and_validate(self, user, form_values: Dict) -> Union[Dict, Dict]:
        expense_payload = {}
        validation_errors = {}
        custom_fields = []

        fyle_expense = FyleExpense(user)

        for key, value in form_values.items():
            custom_field_mappings = {}
            if 'custom_field' in key:
                for inner_key, inner_value in value.items():

                    if inner_value['type'] in ['static_select', 'external_select']:
                        if inner_value['selected_option'] is not None:
                            form_value = inner_value['selected_option']['value']

                        if 'LOCATION' in key:
                            _ , inner_key = key.split('__')
                            if form_value is not None:
                                form_value = fyle_expense.get_place_by_place_id(form_value)

                    if inner_value['type'] in ['multi_static_select', 'multi_external_select']:

                        if 'USER_LIST' in key:
                            _ , inner_key = key.split('__')

                        values_list = []
                        for val in inner_value['selected_options']:
                            values_list.append(val['value'])
                        form_value = values_list

                    elif inner_value['type'] == 'datepicker':

                        if inner_value['selected_date'] is not None and datetime.datetime.strptime(inner_value['selected_date'], '%Y-%m-%d') > datetime.datetime.now():
                            validation_errors[key] = 'Date selected cannot be in future'

                        form_value = inner_value['selected_date']

                    elif inner_value['type'] == 'plain_text_input':

                        if 'TEXT' in key:
                            form_value = inner_value['value'].strip() if inner_value['value'] is not None else None

                        elif 'NUMBER' in key:
                            form_value = inner_value['value']
                            try:
                                form_value = float(inner_value['value']) if inner_value['value'] is not None else None

                                if form_value is not None and form_value < 0:
                                    validation_errors[key] = 'Negative numbers are not allowed'

                                form_value = round(form_value, 2) if value is not None else None

                            except ValueError:
                                validation_errors[key] = 'Only numbers are allowed in this fields'

                    elif inner_value['type'] == 'checkboxes':

                        form_value = False
                        if len(inner_value['selected_options']) > 0:
                            form_value = True

                    custom_field_mappings['name'] = inner_key
                    custom_field_mappings['value'] = form_value

                    custom_fields.append(custom_field_mappings)
            else:
                for inner_key, inner_value in value.items():

                    if inner_value['type'] in ['static_select', 'external_select']:

                        if 'LOCATION' in key:
                            _ , inner_key = key.split('__')
                            place_id = inner_value['selected_option']['value'] if inner_value['selected_option'] is not None else None
                            if place_id is not None:
                                location = fyle_expense.get_place_by_place_id(place_id)
                                if 'locations' in expense_payload:
                                    expense_payload['locations'].append(location)
                                else:
                                    expense_payload['locations'] = [location]
                        elif inner_value['selected_option'] is not None:
                            expense_payload[inner_key] = inner_value['selected_option']['value']

                    if inner_value['type'] == 'multi_static_select':

                        if 'USER_LIST' in key:
                            _ , inner_key = key.split('__')

                        values_list = []
                        for val in inner_value['selected_options']:
                            values_list.append(val['value'])
                        expense_payload[inner_key] = values_list


                    elif inner_value['type'] == 'datepicker':

                        if inner_value['selected_date'] is not None and datetime.datetime.strptime(inner_value['selected_date'], '%Y-%m-%d') > datetime.datetime.now():
                            validation_errors[key] = 'Date selected cannot be for future'

                        expense_payload[inner_key] = inner_value['selected_date']

                    elif inner_value['type'] == 'plain_text_input':
                        if 'TEXT' in key:
                            form_value = inner_value['value'].strip()

                        elif 'NUMBER' in key:
                            form_value = inner_value['value']
                            try:
                                form_value = float(inner_value['value']) if inner_value['value'] is not None else None

                                if form_value is not None and form_value < 0:
                                    validation_errors[key] = 'Negative numbers are not allowed'

                                form_value = round(form_value, 2) if value is not None else None

                            except ValueError:
                                validation_errors[key] = 'Only numbers are allowed in this fields'
                        expense_payload[inner_key] = form_value

                    elif inner_value['type'] == 'checkboxes':

                        expense_payload[inner_key] = False
                        if len(inner_value['selected_options']) > 0:
                            expense_payload[inner_key] = True

        expense_payload['custom_fields'] = custom_fields

        return expense_payload, validation_errors

    def handle_report_approval_from_modal(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        encoded_private_metadata = slack_payload['view']['private_metadata']
        private_metadata = utils.decode_state(encoded_private_metadata)

        # Modifying the slack payload in order to mimic the payload structure sent to "approve_report" function
        slack_payload['actions'] = [
            {
                'value': private_metadata['report_id']
            }
        ]

        slack_payload['message'] = {}
        slack_payload['message']['ts'] = private_metadata['notification_message_ts']
        slack_payload['message']['blocks'] = private_metadata['notification_message_blocks']
        slack_payload['is_approved_from_modal'] = True

        BlockActionHandler().approve_report(slack_payload=slack_payload, user_id=user_id, team_id=team_id)

        return JsonResponse({}, status=200)
