from typing import Any, Dict, List, Union

from fyle_slack_app.models import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.slack.utils import get_slack_client
from fyle_slack_app.libs.utils import decode_state, encode_state
from fyle_slack_app.slack.ui.expenses.messages import expense_dialog_form


def check_project_in_form(form_current_state: Dict, private_metadata: Dict) -> Union[bool, Any]:

    is_project_available = False
    project = None

    if 'project_block' in form_current_state:

        is_project_available = True

        project = private_metadata.get('project')

    return is_project_available, project


def get_custom_field_blocks(current_blocks: List[Dict]) -> List[Dict]:
    custom_field_blocks = []

    for block in current_blocks:
        if 'custom_field' in block['block_id'] or 'additional_field' in block['block_id']:
            custom_field_blocks.append(block)

    if len(custom_field_blocks) == 0:
        custom_field_blocks = None

    return custom_field_blocks


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
        'total_amount': round(exchange_rate * amount, 2)
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

    private_metadata = slack_payload['view']['private_metadata']

    decoded_private_metadata = decode_state(private_metadata)

    decoded_private_metadata['project'] = project

    fields_render_property = decoded_private_metadata['fields_render_property']

    additional_currency_details = decoded_private_metadata.get('additional_currency_details')

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below project input element
    project_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'project_loading_block'), None)
    current_ui_blocks.pop(project_loading_block_index)

    form_current_state = slack_payload['view']['state']['values']

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    fields_render_property['project'] = True
    fields_render_property['cost_center'] = is_cost_center_available

    encoded_private_metadata = encode_state(decoded_private_metadata)

    new_expense_dialog_form = expense_dialog_form(fields_render_property=fields_render_property, selected_project=project, additional_currency_details=additional_currency_details, private_metadata=encoded_private_metadata)

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

    private_metadata = slack_payload['view']['private_metadata']

    decoded_private_metadata = decode_state(private_metadata)

    fields_render_property = decoded_private_metadata['fields_render_property']

    additional_currency_details = decoded_private_metadata.get('additional_currency_details')

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below category input element
    category_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'category_loading_block'), None)
    current_ui_blocks.pop(category_loading_block_index)

    form_current_state = slack_payload['view']['state']['values']

    is_project_available, project = check_project_in_form(form_current_state, decoded_private_metadata)

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    fields_render_property['project'] = is_project_available
    fields_render_property['cost_center'] = is_cost_center_available

    new_expense_dialog_form = expense_dialog_form(fields_render_property=fields_render_property, custom_fields=custom_fields, selected_project=project, additional_currency_details=additional_currency_details, private_metadata=private_metadata)

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)


def handle_currency_select(user: User, team_id: str, slack_payload: str) -> None:

    selected_currency = slack_payload['actions'][0]['selected_option']['value']

    view_id = slack_payload['container']['view_id']

    slack_client = get_slack_client(team_id)

    private_metadata = slack_payload['view']['private_metadata']

    decoded_private_metadata = decode_state(private_metadata)

    fields_render_property = decoded_private_metadata['fields_render_property']

    home_currency = decoded_private_metadata['home_currency']

    form_current_state = slack_payload['view']['state']['values']

    current_ui_blocks = slack_payload['view']['blocks']

    additional_currency_details = {
        'home_currency': home_currency
    }

    if home_currency != selected_currency:
        exchange_rate = 70.12
        amount = form_current_state['NUMBER_default_field_amount_block']['amount']['value']

        additional_currency_details = get_additional_currency_details(amount, home_currency, selected_currency, exchange_rate)

    decoded_private_metadata['additional_currency_details'] = additional_currency_details

    is_project_available, project = check_project_in_form(form_current_state, decoded_private_metadata)

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    custom_fields = get_custom_field_blocks(current_ui_blocks)

    fields_render_property['project'] = is_project_available
    fields_render_property['cost_center'] = is_cost_center_available

    encoded_private_metadata = encode_state(decoded_private_metadata)

    expense_form = expense_dialog_form(selected_project=project, fields_render_property=fields_render_property, additional_currency_details=additional_currency_details, custom_fields=custom_fields, private_metadata=encoded_private_metadata)

    slack_client.views_update(view_id=view_id, view=expense_form)


def handle_amount_entered(user: User, team_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    amount_entered = slack_payload['actions'][0]['value']

    view_id = slack_payload['container']['view_id']

    form_current_state = slack_payload['view']['state']['values']

    private_metadata = slack_payload['view']['private_metadata']

    decoded_private_metadata = decode_state(private_metadata)

    current_ui_blocks = slack_payload['view']['blocks']

    fields_render_property = decoded_private_metadata['fields_render_property']

    home_currency = decoded_private_metadata['home_currency']

    selected_currency = form_current_state['SELECT_default_field_currency_block']['currency']['selected_option']['value']

    exchange_rate = 70.12

    additional_currency_details = get_additional_currency_details(amount_entered, home_currency, selected_currency, exchange_rate)

    decoded_private_metadata['additional_currency_details'] = additional_currency_details

    custom_fields = get_custom_field_blocks(current_ui_blocks)

    is_project_available, project = check_project_in_form(form_current_state, decoded_private_metadata)

    is_cost_center_available = check_cost_centers_in_form(form_current_state)

    fields_render_property['project'] = is_project_available
    fields_render_property['cost_center'] = is_cost_center_available

    encoded_private_metadata = encode_state(decoded_private_metadata)

    expense_form = expense_dialog_form(selected_project=project, fields_render_property=fields_render_property, additional_currency_details=additional_currency_details, custom_fields=custom_fields, private_metadata=encoded_private_metadata)

    slack_client.views_update(view_id=view_id, view=expense_form)
