from typing import Dict

from fyle_slack_app.slack.utils import get_slack_client

from fyle_slack_app.models import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.slack.ui.expenses.messages import expense_dialog_form


def handle_project_select(user: User, team_id: str, project_id: str, view_id: str, slack_payload: Dict) -> None:

    slack_client = get_slack_client(team_id)

    project_query_params = {
        'offset': 0,
        'limit': '1',
        'order': 'created_at.desc',
        'id': 'eq.{}'.format(int(project_id)),
        'is_enabled': 'eq.{}'.format(True)
    }

    fyle_expense = FyleExpense(user)

    project = fyle_expense.get_projects(project_query_params)

    query_params = {
        'offset': 0,
        'limit': '20',
        'order': 'created_at.desc',
        'is_enabled': 'eq.{}'.format(True),
        'system_category': 'not_in.(Unspecified, Per Diem, Mileage, Activity)',
        'id': 'in.{}'.format(tuple(project['data'][0]['category_ids']))
    }

    categories = fyle_expense.get_categories(query_params)

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below project input element
    project_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'project_loading_block'), None)
    current_ui_blocks.pop(project_loading_block_index)


    new_expense_dialog_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, categories=categories)

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)


def handle_category_select(user: User, team_id: str, category_id: str, view_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    custom_fields_query_params = {
        'offset': 0,
        'limit': '20',
        'order': 'created_at.desc',
        'or': '(is_mandatory.eq.{}, and(is_custom.eq.{}, is_mandatory.eq.{}))'.format(True, True, True),
        'column_name': 'not_in.(purpose, txn_dt, vendor_id, cost_center_id)',
        'is_enabled': 'eq.{}'.format(True),
        'category_ids': 'cs.[{}]'.format(int(category_id))
    }

    fyle_expense = FyleExpense(user)

    custom_fields = fyle_expense.get_expense_fields(custom_fields_query_params)

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below category input element
    category_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'category_loading_block'), None)
    current_ui_blocks.pop(category_loading_block_index)

    categories = None

    if 'project_block' in slack_payload['view']['state']['values'] and slack_payload['view']['state']['values']['project_block']['project']['selected_option'] is not None:

        project_id = int(slack_payload['view']['state']['values']['project_block']['project']['selected_option']['value'])

        project_query_params = {
            'offset': 0,
            'limit': '1',
            'order': 'created_at.desc',
            'id': 'eq.{}'.format(int(project_id)),
            'is_enabled': 'eq.{}'.format(True)
        }

        project = fyle_expense.get_projects(project_query_params)

        query_params = {
            'offset': 0,
            'limit': '20',
            'order': 'created_at.desc',
            'is_enabled': 'eq.{}'.format(True),
            'system_category': 'not_in.(Unspecified, Per Diem, Mileage, Activity)',
            'id': 'in.{}'.format(tuple(project['data'][0]['category_ids']))
        }

        categories = fyle_expense.get_categories(query_params)

    new_expense_dialog_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, custom_fields=custom_fields, categories=categories)

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)
