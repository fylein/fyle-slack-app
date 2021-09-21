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

    project = FyleExpense.get_projects(user, project_query_params)

    query_params = {
        'offset': 0,
        'limit': '20',
        'order': 'created_at.desc',
        'is_enabled': 'eq.{}'.format(True),
        'system_category': 'not_in.(Unspecified, Per Diem, Mileage, Activity)',
        'id': 'in.{}'.format(tuple(project['data'][0]['category_ids']))
    }

    categories = FyleExpense.get_categories(user, query_params)

    blocks = slack_payload['view']['blocks']

    # Removing loading info from below project input element
    project_loading_block_index = next((index for (index, d) in enumerate(blocks) if d['block_id'] == 'project_loading_block'), None)
    blocks.pop(project_loading_block_index)

    # Get current UI block for faster rendering, ignore custom field and category blocks since they are dynamically rendered
    current_ui_blocks = []
    for block in blocks:
        if 'custom_field' not in block['block_id'] and 'category_block' not in block['block_id']:
            current_ui_blocks.append(block)

    # Get projects from UI blocks itself, since projects won't be updated in the short span of expense form
    project_options = []
    for block in blocks:
        if block['block_id'] == 'project_block':
            for option in block['element']['options']:
                project_options.append({
                    'display_name': option['text']['text'],
                    'id': int(option['value'])
                })

    projects = {
        'data': project_options,
        'count': len(project_options)
    }

    new_expense_dialog_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, projects=projects, categories=categories)

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


    custom_fields = FyleExpense.get_expense_fields(user, custom_fields_query_params)

    blocks = slack_payload['view']['blocks']

    # Removing loading info from below category input element
    category_loading_block_index = next((index for (index, d) in enumerate(blocks) if d['block_id'] == 'category_loading_block'), None)
    blocks.pop(category_loading_block_index)

    # Get current UI block for faster rendering, ignore custom field and category blocks since they are dynamically rendered
    current_ui_blocks = []
    for block in blocks:
        if 'custom_field' not in block['block_id'] and 'category_block' not in block['block_id']:
            current_ui_blocks.append(block)

    categories = None
    projects = None

    if 'project_block' in slack_payload['view']['state']['values'] and slack_payload['view']['state']['values']['project_block']['project']['selected_option'] is not None:

        project_id = int(slack_payload['view']['state']['values']['project_block']['project']['selected_option']['value'])

        project_query_params = {
            'offset': 0,
            'limit': '1',
            'order': 'created_at.desc',
            'id': 'eq.{}'.format(int(project_id)),
            'is_enabled': 'eq.{}'.format(True)
        }

        project = FyleExpense.get_projects(user, project_query_params)

        query_params = {
            'offset': 0,
            'limit': '20',
            'order': 'created_at.desc',
            'is_enabled': 'eq.{}'.format(True),
            'system_category': 'not_in.(Unspecified, Per Diem, Mileage, Activity)',
            'id': 'in.{}'.format(tuple(project['data'][0]['category_ids']))
        }

        categories = FyleExpense.get_categories(user, query_params)

        blocks = slack_payload['view']['blocks']

        # Get projects from UI blocks itself, since projects won't be updated in the short span of expense form
        project_options = []
        for block in blocks:
            if block['block_id'] == 'project_block':
                for option in block['element']['options']:
                    project_options.append({
                        'display_name': option['text']['text'],
                        'id': int(option['value'])
                    })

        projects = {
            'data': project_options,
            'count': len(project_options)
        }

    new_expense_dialog_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, custom_fields=custom_fields, projects=projects, categories=categories)

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)
