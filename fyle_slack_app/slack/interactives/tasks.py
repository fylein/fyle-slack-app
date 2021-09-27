from typing import Any, Dict, Union

from fyle_slack_app.models import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.slack.utils import get_slack_client
from fyle_slack_app.libs.utils import decode_state, encode_state
from fyle_slack_app.slack.ui.expenses.messages import expense_dialog_form


def check_project_in_form(form_current_state: Dict, fyle_expense: FyleExpense) -> Union[bool, Any]:

    is_project_available = False
    project = None

    if 'project_block' in form_current_state:

        is_project_available = True

        if form_current_state['project_block']['project_id']['selected_option'] is not None:

            project_id = int(form_current_state['project_block']['project_id']['selected_option']['value'])

            project_query_params = {
                'offset': 0,
                'limit': '1',
                'order': 'created_at.desc',
                'id': 'eq.{}'.format(int(project_id)),
                'is_enabled': 'eq.{}'.format(True)
            }

            project = fyle_expense.get_projects(project_query_params)

    return is_project_available, project


def check_cost_centers_in_form(form_current_state) -> bool:

    cost_centers = False

    if 'cost_center_block' in form_current_state and form_current_state['cost_center_block']['cost_center_id']['selected_option'] is not None:
        cost_centers = True

    return cost_centers


def get_additional_currency_details(amount: int, home_currency: str, selected_currency: str, exchange_rate: float) -> Dict:

    if amount is None or len(amount) == 0:
        amount = 0
    else:
        try:
            amount = round(float(amount), 2)
        except ValueError:
            amount = 0

    additional_currency_details = {
        'foreign_currency': selected_currency,
        'home_currency': home_currency,
        'total_amount': exchange_rate * amount
    }

    return additional_currency_details


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

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below project input element
    project_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'project_loading_block'), None)
    current_ui_blocks.pop(project_loading_block_index)

    form_current_state = slack_payload['view']['state']['values']

    fields_render_property = {
        'project': True
    }

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    fields_render_property['cost_center'] = is_cost_center_available

    new_expense_dialog_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, fields_render_property=fields_render_property, selected_project=project)

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

    form_current_state = slack_payload['view']['state']['values']

    is_project_available, project = check_project_in_form(form_current_state, fyle_expense)

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    fields_render_property = {
        'project': is_project_available,
        'cost_center': is_cost_center_available
    }

    new_expense_dialog_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, custom_fields=custom_fields, selected_project=project, fields_render_property=fields_render_property)

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)


def handle_currency_select(user: User, team_id: str, slack_payload: str) -> None:

    selected_currency = slack_payload['actions'][0]['selected_option']['value']

    view_id = slack_payload['container']['view_id']

    slack_client = get_slack_client(team_id)

    private_metadata = decode_state(slack_payload['view']['private_metadata'])

    home_currency = private_metadata['home_currency']

    form_current_state = slack_payload['view']['state']['values']

    additional_currency_details = None

    if home_currency != selected_currency:
        exchange_rate = 70.12
        amount = form_current_state['NUMBER_default_field_amount_block']['amount']['value']

        additional_currency_details = get_additional_currency_details(amount, home_currency, selected_currency, exchange_rate)

    private_metadata['additional_currency_details'] = additional_currency_details

    current_ui_blocks = slack_payload['view']['blocks']

    fyle_expense = FyleExpense(user)

    is_project_available, project = check_project_in_form(form_current_state, fyle_expense)

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    fields_render_property = {
        'project': is_project_available,
        'cost_center': is_cost_center_available
    }

    expense_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, selected_project=project, fields_render_property=fields_render_property, additional_currency_details=additional_currency_details)

    expense_form['private_metadata'] = encode_state(private_metadata)

    slack_client.views_update(view_id=view_id, view=expense_form)


def handle_amount_entered(user: User, team_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    amount_entered = slack_payload['actions'][0]['value']

    view_id = slack_payload['container']['view_id']

    form_current_state = slack_payload['view']['state']['values']

    private_metadata = decode_state(slack_payload['view']['private_metadata'])

    home_currency = private_metadata['home_currency']

    selected_currency = form_current_state['SELECT_default_field_currency_block']['currency']['selected_option']['value']

    exchange_rate = 70.12

    additional_currency_details = get_additional_currency_details(amount_entered, home_currency, selected_currency, exchange_rate)

    current_ui_blocks = slack_payload['view']['blocks']

    fyle_expense = FyleExpense(user)

    is_project_available, project = check_project_in_form(form_current_state, fyle_expense)

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    fields_render_property = {
        'project': is_project_available,
        'cost_center': is_cost_center_available
    }

    expense_form = expense_dialog_form(current_ui_blocks=current_ui_blocks, selected_project=project, fields_render_property=fields_render_property, additional_currency_details=additional_currency_details)

    slack_client.views_update(view_id=view_id, view=expense_form)
