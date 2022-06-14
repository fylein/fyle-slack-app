import datetime

from typing import Callable, List, Dict, Union
from dateutil.parser import parse

from django.http.response import JsonResponse
from django.core.cache import cache

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
        expense_id = None
        message_ts = None
        if form_metadata is not None:
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
        # pylint: disable=unused-variable
        expense_id = slack_payload['view']['private_metadata']

        if 'TEXT_add_to_new_report_block' in add_expense_to_report_form_values:
            # pylint: disable=unused-variable
            report_name = add_expense_to_report_form_values['TEXT_add_to_new_report_block']['report_name']['value']

        elif 'SELECT_add_to_existing_report_block' in add_expense_to_report_form_values:
            # pylint: disable=unused-variable
            existing_report_id = add_expense_to_report_form_values['SELECT_add_to_existing_report_block']['existing_report']['selected_option']['value']

        encoded_private_metadata = slack_payload['view']['private_metadata']
        # pylint: disable=unused-variable
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


    def get_travel_class_list(self, expense_payload: Dict, block_id: str, form_value: str) -> List[Dict]:
        # This method will give you the travel class object - travel_classes field
        travel_classes = [None, None]

        if 'travel_classes' in expense_payload:
            travel_classes = expense_payload['travel_classes']

        if '_journey_travel_class' in block_id:
            travel_classes[0] = form_value
        elif '_return_travel_class' in block_id:
            if len(travel_classes) == 1:
                travel_classes.append(form_value)
            else:
                travel_classes[1] = form_value

        return travel_classes


    def append_into_expense_payload_for_upsert_expense(self, expense_payload: Dict, expense_field_key: str, form_value: any, block_id: str) -> Dict:
        # expense_payload is used as the payload which is sent to POST request of /spender/expenses API
        # Only single expense field will be appended to the expense payload at a time
        # Can refer the expense post payload structure from here: https://docs.fylehq.com/docs/fyle-platform-docs/ -> Spender APIs -> Expenses -> Crreate or upadte expense (POST)

        if 'from_dt' in block_id:
            expense_payload['started_at'] = form_value

        elif 'to_dt' in block_id:
            expense_payload['ended_at'] = form_value

        elif 'custom_field' in block_id:
            custom_field = {
                'name': expense_field_key,
                'value': form_value
            }
            if 'custom_fields' in expense_payload:
                expense_payload['custom_fields'].append(custom_field)
            else:
                expense_payload['custom_fields'] = [custom_field]

        elif 'LOCATION' in block_id:
            if 'locations' in expense_payload:
                expense_payload['locations'].append(form_value)
            else:
                expense_payload['locations'] = [form_value]

        elif 'travel_class' in block_id:
            travel_classes = self.get_travel_class_list(expense_payload, block_id, form_value)
            expense_payload['travel_classes'] = travel_classes

        else:
            expense_payload[expense_field_key] = form_value

        return expense_payload


    def extract_form_values_and_validate(self, user, form_values: Dict) -> Union[Dict, Dict]:
        expense_payload = {}
        validation_errors = {}

        fyle_expense = FyleExpense(user)
        for block_id, value in form_values.items():
            for expense_field_key, form_detail in value.items():
                form_value = None
                if form_detail['type'] in ['static_select', 'external_select']:
                    expense_field_key, form_value = self.extract_select_field_detail(
                        expense_field_key,
                        form_detail,
                        block_id,
                        fyle_expense
                    )

                if form_detail['type'] in ['multi_static_select', 'multi_external_select']:
                    expense_field_key, form_value = self.extract_multi_select_field(expense_field_key, form_detail, block_id)

                elif form_detail['type'] == 'datepicker':
                    form_value, validation_errors = self.extract_and_validate_date_field(form_detail, block_id, validation_errors)

                elif form_detail['type'] == 'plain_text_input':
                    form_value, validation_errors = self.extract_and_validate_text_field(form_detail, block_id, validation_errors)

                elif form_detail['type'] == 'checkboxes':
                    form_value = self.extract_checkbox_field(form_detail)
                
                if form_value is not None:                                        
                    expense_payload = self.append_into_expense_payload_for_upsert_expense(
                        expense_payload,
                        expense_field_key,
                        form_value,
                        block_id
                    )

        return expense_payload, validation_errors

    def extract_select_field_detail(self, expense_field_key: str, form_detail: Dict, block_id: str, fyle_expense: FyleExpense):
        form_value = None
        if form_detail['selected_option'] is not None:
            form_value = form_detail['selected_option']['value']

        if 'LOCATION' in block_id:
            _ , expense_field_key = block_id.split('__')
            place_id = form_detail['selected_option']['value'] if form_detail['selected_option'] is not None else None
            if place_id is not None:
                location = fyle_expense.get_place_by_place_id(place_id)
                form_value = location
                form_value['display'] = location['formatted_address']

        if 'travel_class' in block_id:
            travel_class = form_detail['selected_option']['value'] if form_detail['selected_option'] is not None else None
            form_value = travel_class

        return expense_field_key, form_value

    def extract_multi_select_field(self, expense_field_key: str, form_detail: Dict, block_id: str):
        if 'USER_LIST' in block_id:
            _ , expense_field_key = block_id.split('__')
        values_list = []
        for val in form_detail['selected_options']:
            values_list.append(val['value'])
        form_value = values_list
        return expense_field_key, form_value

    def extract_and_validate_date_field(self, form_detail: Dict, block_id: str, validation_errors: Dict):
        if form_detail['selected_date'] is not None and datetime.datetime.strptime(form_detail['selected_date'], '%Y-%m-%d') > datetime.datetime.now():
            validation_errors[block_id] = 'Date selected cannot be in future'
        form_value = form_detail['selected_date']
        if form_value is not None:
            form_value = parse(form_value).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return form_value, validation_errors

    def extract_and_validate_text_field(self, form_detail: Dict, block_id: str, validation_errors: Dict):
        if 'TEXT' in block_id:
            form_value = form_detail['value'].strip() if form_detail['value'] is not None else None

        elif 'NUMBER' in block_id:
            form_value = form_detail['value']
            try:
                form_value = float(form_detail['value']) if form_detail['value'] is not None else None
                if form_value is not None and form_value < 0:
                    validation_errors[block_id] = 'Negative numbers are not allowed'
                form_value = round(form_value, 2) if form_value is not None else None
            except ValueError:
                validation_errors[block_id] = 'Only numbers are allowed in this fields'
        return form_value, validation_errors

    def extract_checkbox_field(self, form_detail: Dict):
        form_value = False
        if len(form_detail['selected_options']) > 0:
            form_value = True
        return form_value

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
