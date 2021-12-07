from typing import Dict, List

from django.core.cache import cache

from fyle_slack_app.models import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.slack.utils import get_slack_client
from fyle_slack_app.slack.ui.expenses.messages import expense_dialog_form
from fyle_slack_app.slack.ui.expenses import messages as expense_messages


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


def handle_project_selection(user: User, team_id: str, project_id: str, view_id: str, slack_payload: Dict) -> None:

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

    project = project['data'][0]

    project = {
        'id': project['id'],
        'name': project['name'],
        'display_name': project['display_name'],
        'sub_project': project['sub_project'],
        'category_ids': project['category_ids']
    }

    current_expense_form_details = fyle_expense.get_current_expense_form_details(slack_payload)

    cache_key = '{}.form_metadata'.format(slack_payload['view']['id'])
    form_metadata = cache.get(cache_key)

    # Removing custom fields when project is selected
    current_expense_form_details['custom_fields'] = None

    current_expense_form_details['selected_project'] = project

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below project input element
    project_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'project_loading_block'), None)
    current_ui_blocks.pop(project_loading_block_index)

    form_metadata['project'] = project

    cache.set(cache_key, form_metadata)

    new_expense_dialog_form = expense_dialog_form(
        **current_expense_form_details
    )

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)


def handle_category_selection(user: User, team_id: str, category_id: str, view_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    fyle_expense = FyleExpense(user)

    custom_fields = fyle_expense.get_custom_fields_by_category_id(category_id)

    current_expense_form_details = fyle_expense.get_current_expense_form_details(slack_payload)

    current_expense_form_details['custom_fields'] = custom_fields

    current_ui_blocks = slack_payload['view']['blocks']

    # Removing loading info from below category input element
    category_loading_block_index = next((index for (index, d) in enumerate(current_ui_blocks) if d['block_id'] == 'category_loading_block'), None)
    current_ui_blocks.pop(category_loading_block_index)

    new_expense_dialog_form = expense_dialog_form(
        **current_expense_form_details
    )

    slack_client.views_update(view_id=view_id, view=new_expense_dialog_form)


def handle_currency_selection(selected_currency: str, view_id: str, team_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    current_expense_form_details = FyleExpense.get_current_expense_form_details(slack_payload)

    cache_key = '{}.form_metadata'.format(slack_payload['view']['id'])
    form_metadata = cache.get(cache_key)

    additional_currency_details = current_expense_form_details['additional_currency_details']

    home_currency = additional_currency_details['home_currency']

    additional_currency_details = {
        'home_currency': home_currency
    }

    if home_currency != selected_currency:
        form_current_state = slack_payload['view']['state']['values']
        exchange_rate = 70.12
        amount = form_current_state['NUMBER_default_field_amount_block']['amount']['value']
        additional_currency_details = get_additional_currency_details(amount, home_currency, selected_currency, exchange_rate)

    current_expense_form_details['additional_currency_details'] = additional_currency_details

    form_metadata['additional_currency_details'] = additional_currency_details

    cache.set(cache_key, form_metadata)

    expense_form = expense_dialog_form(
        **current_expense_form_details
    )

    slack_client.views_update(view_id=view_id, view=expense_form)


def handle_amount_entered(amount_entered: float, view_id: str, team_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    form_current_state = slack_payload['view']['state']['values']

    selected_currency = form_current_state['SELECT_default_field_currency_block']['currency']['selected_option']['value']

    current_expense_form_details = FyleExpense.get_current_expense_form_details(slack_payload)

    cache_key = '{}.form_metadata'.format(slack_payload['view']['id'])
    form_metadata = cache.get(cache_key)

    exchange_rate = 70.12

    home_currency = current_expense_form_details['additional_currency_details']['home_currency']

    additional_currency_details = get_additional_currency_details(amount_entered, home_currency, selected_currency, exchange_rate)

    current_expense_form_details['additional_currency_details'] = additional_currency_details

    form_metadata['additional_currency_details'] = additional_currency_details

    cache.set(cache_key, form_metadata)

    expense_form = expense_dialog_form(
        **current_expense_form_details
    )

    slack_client.views_update(view_id=view_id, view=expense_form)


def handle_edit_expense(user: User, expense_id: str, team_id: str, view_id: str, slack_payload: List[Dict]) -> None:

    slack_client = get_slack_client(team_id)

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

    custom_fields = fyle_expense.get_custom_fields_by_category_id(expense['category_id'])

    expense_form_details = FyleExpense.get_expense_form_details(user, view_id)

    cache_key = '{}.form_metadata'.format(slack_payload['view']['id'])
    form_metadata = cache.get(cache_key)

    # Add additional metadata to differentiate create and edit expense
    # message_ts to update message in edit case
    form_metadata['expense_id'] = expense_id
    form_metadata['message_ts'] = slack_payload['container']['message_ts']

    cache.set(cache_key, form_metadata)

    expense_form = expense_dialog_form(
        expense=expense,
        custom_fields=custom_fields,
        **expense_form_details
    )

    slack_client.views_update(view=expense_form, view_id=view_id)


def handle_submit_report_dialog(user: User, team_id: str, report_id: str, view_id: str):

    slack_client = get_slack_client(team_id)

    fyle_expense = FyleExpense(user)

    expense_query_params = {
        'offset': 0,
        'limit': '30',
        'order': 'created_at.desc',
        'report_id': 'eq.{}'.format(report_id)
    }

    expenses = fyle_expense.get_expenses(query_params=expense_query_params)

    report_query_params = {
        'offset': 0,
        'limit': '1',
        'order': 'created_at.desc',
        'id': 'eq.{}'.format(report_id)
    }

    report = fyle_expense.get_reports(query_params=report_query_params)

    add_expense_to_report_dialog = expense_messages.get_view_report_details_dialog(user, report=report['data'][0], expenses=expenses['data'])

    add_expense_to_report_dialog['private_metadata'] = report_id

    slack_client.views_update(view_id=view_id, view=add_expense_to_report_dialog)
