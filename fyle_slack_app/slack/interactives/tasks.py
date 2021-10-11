from typing import Dict, List

from fyle_slack_app.models import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.fyle.utils import get_fyle_profile
from fyle_slack_app.slack.utils import get_slack_client
from fyle_slack_app.libs.utils import decode_state, encode_state
from fyle_slack_app.slack.ui.expenses.messages import expense_dialog_form


def get_custom_field_blocks(current_blocks: List[Dict]) -> List[Dict]:
    custom_field_blocks = []

    for block in current_blocks:
        if 'custom_field' in block['block_id'] or 'additional_field' in block['block_id']:
            custom_field_blocks.append(block)

    if len(custom_field_blocks) == 0:
        custom_field_blocks = None

    return custom_field_blocks


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

    project = project['data'][0]

    project = {
        'id': project['id'],
        'name': project['name'],
        'display_name': project['display_name'],
        'sub_project': project['sub_project'],
        'category_ids': project['category_ids']
    }

    decoded_private_metadata['project'] = project

    fields_render_property = decoded_private_metadata['fields_render_property']

    additional_currency_details = decoded_private_metadata.get('additional_currency_details')

    add_to_report = decoded_private_metadata.get('add_to_report')

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below project input element
    project_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'project_loading_block'), None)
    current_ui_blocks.pop(project_loading_block_index)

    encoded_private_metadata = encode_state(decoded_private_metadata)

    new_expense_dialog_form = expense_dialog_form(
        fields_render_property=fields_render_property,
        selected_project=project,
        additional_currency_details=additional_currency_details,
        add_to_report=add_to_report,
        private_metadata=encoded_private_metadata
    )

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)


def handle_category_select(user: User, team_id: str, category_id: str, view_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    fyle_expense = FyleExpense(user)

    custom_fields = fyle_expense.get_custom_fields_by_category_id(category_id)

    private_metadata = slack_payload['view']['private_metadata']

    decoded_private_metadata = decode_state(private_metadata)

    fields_render_property = decoded_private_metadata['fields_render_property']

    additional_currency_details = decoded_private_metadata.get('additional_currency_details')

    add_to_report = decoded_private_metadata.get('add_to_report')

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below category input element
    category_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'category_loading_block'), None)
    current_ui_blocks.pop(category_loading_block_index)

    project = decoded_private_metadata.get('project')

    new_expense_dialog_form = expense_dialog_form(
        fields_render_property=fields_render_property,
        custom_fields=custom_fields,
        selected_project=project,
        additional_currency_details=additional_currency_details,
        add_to_report=add_to_report,
        private_metadata=private_metadata
    )

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)


def handle_currency_select(user: User, team_id: str, slack_payload: str) -> None:

    selected_currency = slack_payload['actions'][0]['selected_option']['value']

    view_id = slack_payload['container']['view_id']

    slack_client = get_slack_client(team_id)

    private_metadata = slack_payload['view']['private_metadata']

    decoded_private_metadata = decode_state(private_metadata)

    fields_render_property = decoded_private_metadata['fields_render_property']

    add_to_report = decoded_private_metadata.get('add_to_report')

    home_currency = decoded_private_metadata['additional_currency_details']['home_currency']

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

    project = decoded_private_metadata.get('project')

    custom_fields = get_custom_field_blocks(current_ui_blocks)

    encoded_private_metadata = encode_state(decoded_private_metadata)

    expense_form = expense_dialog_form(
        selected_project=project,
        fields_render_property=fields_render_property,
        additional_currency_details=additional_currency_details,
        custom_fields=custom_fields,
        add_to_report=add_to_report,
        private_metadata=encoded_private_metadata
    )

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

    add_to_report = decoded_private_metadata.get('add_to_report')

    home_currency = decoded_private_metadata['additional_currency_details']['home_currency']

    selected_currency = form_current_state['SELECT_default_field_currency_block']['currency']['selected_option']['value']

    exchange_rate = 70.12

    additional_currency_details = get_additional_currency_details(amount_entered, home_currency, selected_currency, exchange_rate)

    decoded_private_metadata['additional_currency_details'] = additional_currency_details

    custom_fields = get_custom_field_blocks(current_ui_blocks)

    project = decoded_private_metadata.get('project')

    encoded_private_metadata = encode_state(decoded_private_metadata)

    expense_form = expense_dialog_form(
        selected_project=project,
        fields_render_property=fields_render_property,
        additional_currency_details=additional_currency_details,
        add_to_report=add_to_report,
        custom_fields=custom_fields,
        private_metadata=encoded_private_metadata
    )

    slack_client.views_update(view_id=view_id, view=expense_form)


def handle_edit_expense(user: User, team_id: str, view_id: str, slack_payload: List[Dict]) -> None:

    fyle_expense = FyleExpense(user)

    slack_client = get_slack_client(team_id)

    fyle_profile = get_fyle_profile(user.fyle_refresh_token)

    expense_id = slack_payload['actions'][0]['value']
    expense_id = 'txCCVGvNpDMM'

    fyle_expense = FyleExpense(user)

    expense_query_params = {
        'offset': 0,
        'limit': '1',
        'order': 'created_at.desc',
        'id': 'eq.{}'.format(expense_id)
    }

    expense = fyle_expense.get_expenses(query_params=expense_query_params)

    expense = expense['data'][0]

    home_currency = fyle_profile['org']['currency']

    is_project_available = False
    is_cost_centers_available = False

    projects_query_params = {
        'offset': 0,
        'limit': '1',
        'order': 'created_at.desc',
        'is_enabled': 'eq.{}'.format(True)
    }

    projects = fyle_expense.get_projects(projects_query_params)

    is_project_available = True if projects['count'] > 0 else False

    cost_centers_query_params = {
        'offset': 0,
        'limit': '1',
        'order': 'created_at.desc',
        'is_enabled': 'eq.{}'.format(True)
    }

    cost_centers = fyle_expense.get_cost_centers(cost_centers_query_params)

    is_cost_centers_available = True if cost_centers['count'] > 0 else False

    custom_fields = fyle_expense.get_custom_fields_by_category_id(expense['category_id'])

    fields_render_property = {
        'project': is_project_available,
        'cost_center': is_cost_centers_available
    }

    additional_currency_details = {
        'home_currency': home_currency
    }

    add_to_report = 'existing_report'

    private_metadata = {
        'fields_render_property': fields_render_property,
        'additional_currency_details': additional_currency_details,
        'expense_id': expense_id,
        'add_to_report': add_to_report,
        'message_ts': slack_payload['container']['message_ts']
    }

    encoded_metadata = encode_state(private_metadata)

    expense_form = expense_dialog_form(
        expense=expense,
        fields_render_property=fields_render_property,
        private_metadata=encoded_metadata,
        additional_currency_details=additional_currency_details,
        add_to_report=add_to_report,
        custom_fields=custom_fields
    )

    slack_client.views_update(view=expense_form, view_id=view_id)
