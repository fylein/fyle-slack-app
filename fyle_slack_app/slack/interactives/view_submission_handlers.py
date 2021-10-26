import datetime
import json
from typing import Callable, Dict, Union

from django.http.response import JsonResponse

from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.models import User
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.libs import utils
from fyle_slack_app.slack.ui.expenses import messages as expense_messages


class ViewSubmissionHandler:

    _view_submission_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_view_submission_handlers(self):
        self._view_submission_handlers = {
            'upsert_expense': self.handle_upsert_expense,
            'submit_report': self.handle_submit_report,
            'add_expense_to_report': self.handle_add_expense_to_report
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
        print('REACHED CREATE EXPENSE -> ', form_values)

        private_metadata = utils.decode_state(slack_payload['view']['private_metadata'])

        expense_details, validation_errors = self.extract_form_values_and_validate(form_values)

        expense_id = private_metadata.get('expense_id')

        message_ts = private_metadata.get('message_ts')

        if expense_id is not None:
            expense_details['id'] = expense_id

        print('VALIDATION ERRORS -> ', validation_errors)

        # If valdiation errors are present then return errors
        if bool(validation_errors) is True:
            return JsonResponse({
                'response_action': 'errors',
                'errors': validation_errors
            })

        print('EXPENSE -> ', json.dumps(expense_details, indent=2))

        slack_client = slack_utils.get_slack_client(team_id)

        # expense_id = 'txCCVGvNpDMM'
        expense_id = 'tx0mjvrfuizk'
        # expense_id = 'txjNT3H5dTw1'

        fyle_expense = FyleExpense(user)

        expense_query_params = {
            'offset': 0,
            'limit': '1',
            'order': 'created_at.desc',
            'id': 'eq.{}'.format(expense_id)
        }

        expense = fyle_expense.get_expenses(query_params=expense_query_params)

        view_expense_message = expense_messages.view_expense_message(expense['data'][0], user)

        if expense_id is None or message_ts is None:
            slack_client.chat_postMessage(channel=user.slack_dm_channel_id, blocks=view_expense_message)
        else:
            slack_client.chat_update(channel=user.slack_dm_channel_id, blocks=view_expense_message, ts=message_ts)

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


        return JsonResponse({})


    def extract_form_values_and_validate(self, form_values: Dict) -> Union[Dict, Dict]:
        expense_details = {}
        validation_errors = {}
        custom_fields = []

        for key, value in form_values.items():
            custom_field_mappings = {}
            if 'custom_field' in key:
                for inner_key, inner_value in value.items():

                    if inner_value['type'] in ['static_select', 'external_select']:
                        if inner_value['selected_option'] is not None:
                            value = inner_value['selected_option']['value']

                    if inner_value['type'] == 'multi_static_select':

                        values_list = []
                        for val in inner_value['selected_options']:
                            values_list.append(val['value'])
                        value = values_list

                    elif inner_value['type'] == 'datepicker':

                        if datetime.datetime.strptime(inner_value['selected_date'], '%Y-%m-%d') > datetime.datetime.now():
                            validation_errors[key] = 'Date selected cannot be in future'

                        value = inner_value['selected_date']

                    elif inner_value['type'] == 'plain_text_input':

                        if 'TEXT' in key:
                            value = inner_value['value'].strip()

                        elif 'NUMBER' in key:
                            value = inner_value['value']
                            try:
                                value = float(inner_value['value'])

                                if value < 0:
                                    validation_errors[key] = 'Negative numbers are not allowed'

                                value = round(value, 2)

                            except ValueError:
                                validation_errors[key] = 'Only numbers are allowed in this fields'

                    elif inner_value['type'] == 'checkboxes':

                        value = False
                        if len(inner_value['selected_options']) > 0:
                            value = True

                    custom_field_mappings['name'] = inner_key
                    custom_field_mappings['value'] = value

                    custom_fields.append(custom_field_mappings)
            else:
                for inner_key, inner_value in value.items():

                    if inner_value['type'] in ['static_select', 'external_select']:
                        if inner_value['selected_option'] is not None:
                            expense_details[inner_key] = inner_value['selected_option']['value']

                    if inner_value['type'] == 'multi_static_select':

                        values_list = []
                        for val in inner_value['selected_options']:
                            values_list.append(val['value'])
                        expense_details[inner_key] = values_list


                    elif inner_value['type'] == 'datepicker':

                        if datetime.datetime.strptime(inner_value['selected_date'], '%Y-%m-%d') > datetime.datetime.now():
                            validation_errors[key] = 'Date selected cannot be for future'

                        expense_details[inner_key] = inner_value['selected_date']

                    elif inner_value['type'] == 'plain_text_input':
                        if 'TEXT' in key:
                            value = inner_value['value'].strip()

                        elif 'NUMBER' in key:
                            value = inner_value['value']
                            try:
                                value = float(inner_value['value'])

                                if value < 0:
                                    validation_errors[key] = 'Negative numbers are not allowed'

                                value = round(value, 2)

                            except ValueError:
                                validation_errors[key] = 'Only numbers are allowed in this fields'
                        expense_details[inner_key] = value

                    elif inner_value['type'] == 'checkboxes':

                        expense_details[inner_key] = False
                        if len(inner_value['selected_options']) > 0:
                            expense_details[inner_key] = True

        expense_details['custom_fields'] = custom_fields

        return expense_details, validation_errors
