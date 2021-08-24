import json
from django.http.response import JsonResponse


def handle_view_submission(slack_payload, user_id, team_id):
    callback_id = slack_payload['view']['callback_id']

    if callback_id == 'create_expense':
        form_values = slack_payload['view']['state']['values']
        print("REACHED CREATE EXPENSE")

        expense_mapping = {}

        for key, value in form_values.items():
            for inner_key, inner_value in value.items():
                if inner_value['type'] == 'static_select':
                    expense_mapping[inner_key] = inner_value['selected_option']['value']
                elif inner_value['type'] == 'datepicker':
                    expense_mapping[inner_key] = inner_value['selected_date']
                elif inner_value['type'] == 'plain_text_input':
                    expense_mapping[inner_key] = inner_value['value']

        print('EXPENSE -> ', json.dumps(expense_mapping, indent=2))
    return JsonResponse({})
