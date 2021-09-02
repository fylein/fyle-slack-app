import json

from typing import Callable, Dict

from django.http.response import JsonResponse

from fyle_slack_app.slack import utils as slack_utils

class ViewSubmissionHandler:

    _view_submission_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_view_submission_handlers(self):
        self._view_submission_handlers = {
            'create_expense': self.handle_create_expense
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


    def handle_create_expense(self, slack_payload: Dict, user_id: str, team_id: str):
        callback_id = slack_payload['view']['callback_id']

        if callback_id == 'create_expense':
            form_values = slack_payload['view']['state']['values']
            print('REACHED CREATE EXPENSE -> ', form_values)

            expense_mapping = {}
            custom_fields = []

            for key, value in form_values.items():
                custom_field_mappings = {}
                if 'custom_field' in key:
                    for inner_key, inner_value in value.items():
                        if inner_value['type'] == 'static_select':
                            custom_field_mappings[inner_key] = inner_value['selected_option']['value']
                        if inner_value['type'] == 'multi_static_select':
                            values_list = []
                            for val in inner_value['selected_options']:
                                values_list.append(val['value'])
                            custom_field_mappings[inner_key] = values_list
                        elif inner_value['type'] == 'datepicker':
                            custom_field_mappings[inner_key] = inner_value['selected_date']
                        elif inner_value['type'] == 'plain_text_input':
                            custom_field_mappings[inner_key] = inner_value['value']
                        elif inner_value['type'] == 'checkboxes':
                            custom_field_mappings[inner_key] = False
                            if len(inner_value['selected_options']) > 0:
                                custom_field_mappings[inner_key] = True

                        custom_fields.append(custom_field_mappings)
                else:
                    for inner_key, inner_value in value.items():
                        if inner_value['type'] == 'static_select':
                            expense_mapping[inner_key] = inner_value['selected_option']['value']
                        if inner_value['type'] == 'multi_static_select':
                            values_list = []
                            for val in inner_value['selected_options']:
                                values_list.append(val['value'])
                            expense_mapping[inner_key] = values_list
                        elif inner_value['type'] == 'datepicker':
                            expense_mapping[inner_key] = inner_value['selected_date']
                        elif inner_value['type'] == 'plain_text_input':
                            expense_mapping[inner_key] = inner_value['value']
                        elif inner_value['type'] == 'checkboxes':
                            expense_mapping[inner_key] = False
                            if len(inner_value['selected_options']) > 0:
                                expense_mapping[inner_key] = True

            expense_mapping['custom_fields'] = custom_fields

            print('EXPENSE -> ', json.dumps(expense_mapping, indent=2))

            slack_client = slack_utils.get_slack_client(team_id)
            blocks = [
                {
                    'type': 'section',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Expense created successfully :clipboard:',
                        'emoji': True,
                    },
                },
                {
                    'type': 'section',
                    'fields': [
                        {'type': 'mrkdwn', 'text': '*Amount*: \n {} {}'.format(expense_mapping['currency'], expense_mapping['amount'])},
                        {'type': 'mrkdwn', 'text': '*Merchant*: \n {}'.format(expense_mapping['merchant'])},
                    ],
                },
                {
                    'type': 'section',
                    'fields': [
                        {'type': 'mrkdwn', 'text': '*Date of Spend*: \n {}'.format(expense_mapping['spent_at'])},
                        {'type': 'mrkdwn', 'text': '*Purpose*: \n {}'.format(expense_mapping['purpose'])},
                    ],
                },
                {
                    'type': 'actions',
                    'elements': [
                        {
                            'type': 'button',
                            'text': {
                                'type': 'plain_text',
                                'text': 'Edit Expense',
                                'emoji': True,
                            },
                            'value': 'tx123456',
                            'action_id': 'edit_expense',
                        }
                    ],
                },
                {
                    'type': 'context',
                    'block_id': 'tx123456',
                    'elements': [
                        {
                            'type': 'plain_text',
                            'text': 'Powered by Fyle',
                            'emoji': True,
                        }
                    ],
                },
            ]

            slack_client.chat_postMessage(channel='D01K1L9UHBP', blocks=blocks)
        return JsonResponse({})
