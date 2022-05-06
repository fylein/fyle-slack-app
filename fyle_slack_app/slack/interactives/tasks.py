from typing import Dict, List

from django.core.cache import cache

from fyle_slack_app.models import User
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.slack.utils import get_slack_client
from fyle_slack_app.slack.ui.expenses.messages import expense_dialog_form
from fyle_slack_app.slack.ui.expenses import messages as expense_messages
from fyle_slack_app.libs import utils, logger
from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval
from fyle_slack_app.models import User, UserFeedbackResponse
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.ui.feedbacks import messages as feedback_messages
from fyle_slack_app.slack.ui.modals import messages as modal_messages
from fyle_slack_app.slack.ui import common_messages
from fyle_slack_app import tracking
from fyle.platform import exceptions


logger = logger.get_logger(__name__)

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


def handle_project_selection(user: User, team_id: str, project: Dict, view_id: str, slack_payload: Dict) -> None:
    slack_client = get_slack_client(team_id)
    fyle_expense = FyleExpense(user)

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


def handle_currency_selection(user: User, selected_currency: str, view_id: str, team_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    fyle_expense = FyleExpense(user)

    current_expense_form_details = fyle_expense.get_current_expense_form_details(slack_payload)

    cache_key = '{}.form_metadata'.format(slack_payload['view']['id'])
    form_metadata = cache.get(cache_key)

    additional_currency_details = current_expense_form_details['additional_currency_details']

    home_currency = additional_currency_details['home_currency']

    additional_currency_details = {
        'home_currency': home_currency
    }

    if home_currency != selected_currency:
        form_current_state = slack_payload['view']['state']['values']
        exchange_rate = fyle_expense.get_exchange_rate(selected_currency, home_currency)
        amount = form_current_state['NUMBER_default_field_amount_block']['claim_amount']['value']
        additional_currency_details = get_additional_currency_details(amount, home_currency, selected_currency, exchange_rate)

    current_expense_form_details['additional_currency_details'] = additional_currency_details

    form_metadata['additional_currency_details'] = additional_currency_details

    cache.set(cache_key, form_metadata)

    expense_form = expense_dialog_form(
        **current_expense_form_details
    )

    slack_client.views_update(view_id=view_id, view=expense_form)


def handle_amount_entered(user: User, amount_entered: float, view_id: str, team_id: str, slack_payload: str) -> None:

    slack_client = get_slack_client(team_id)

    fyle_expense = FyleExpense(user)

    form_current_state = slack_payload['view']['state']['values']

    selected_currency = form_current_state['SELECT_default_field_currency_block']['currency']['selected_option']['value']

    current_expense_form_details = fyle_expense.get_current_expense_form_details(slack_payload)

    cache_key = '{}.form_metadata'.format(slack_payload['view']['id'])
    form_metadata = cache.get(cache_key)

    home_currency = current_expense_form_details['additional_currency_details']['home_currency']

    exchange_rate = fyle_expense.get_exchange_rate(selected_currency, home_currency)

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

    cache_key = '{}.form_metadata'.format(view_id)
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


def handle_upsert_expense(user: User, team_id: str, expense_payload: Dict, expense_id: str, message_ts: str):
    slack_client = get_slack_client(team_id)
    fyle_expense = FyleExpense(user)

    expense = fyle_expense.upsert_expense(expense_payload, user.fyle_refresh_token)
    view_expense_message = expense_messages.view_expense_message(expense, user)

    if expense_id is None or message_ts is None:
        slack_client.chat_postMessage(channel=user.slack_dm_channel_id, blocks=view_expense_message)
    else:
        slack_client.chat_update(channel=user.slack_dm_channel_id, blocks=view_expense_message, ts=message_ts)


def handle_feedback_submission(user: User, team_id: str, form_values: Dict, private_metadata: Dict):
    user_feedback_id = private_metadata['user_feedback_id']
    feedback_message_ts = private_metadata['feedback_message_ts']
    feedback_trigger = private_metadata['feedback_trigger']

    slack_client = slack_utils.get_slack_client(team_id)

    rating = int(form_values['rating_block']['rating']['selected_option']['value'])
    comment = form_values['comment_block']['comment']['value']

    # Register user feedback response
    UserFeedbackResponse.create_user_feedback_response(
        user_feedback_id=user_feedback_id,
        user=user,
        rating=rating,
        comment=comment
    )

    post_feedback_submission_message = feedback_messages.get_post_feedback_submission_message()

    # Upadate original feedback message
    slack_client.chat_update(
        text='Thanks for submitting the feedback',
        blocks=post_feedback_submission_message,
        channel=user.slack_dm_channel_id,
        ts=feedback_message_ts
    )

    user_email = user.email
    event_data = {
        'feedback_trigger': feedback_trigger,
        'comment': comment,
        'rating': rating,
        'email': user_email,
        'slack_user_id': user.slack_user_id
    }

    tracking.identify_user(user_email)
    tracking.track_event(user_email, 'Feedback Submitted', event_data)


def handle_fetching_of_report_and_its_expenses(user: User, team_id: str, private_metadata: Dict, modal_view_id: str):
    slack_client = slack_utils.get_slack_client(team_id)

    # Fetch the report
    fyle_report_approval = FyleReportApproval(user)

    try:
        report = fyle_report_approval.get_report_by_id(private_metadata['report_id'])
        report = report['data']
    except exceptions.NotFoundItemError as error:
        logger.error('Report not found with id -> %s', private_metadata['report_id'])
        logger.error('Error -> %s', error)
        # None here means report is deleted/doesn't exist
        report = None

    if report is None:
        # Show no report-access message
        no_report_access_message = 'Looks like you no longer have access to this expense report :face_with_head_bandage:'
        report_notification_message = common_messages.get_updated_approval_notification_message(notification_message=private_metadata['notification_message_blocks'], custom_message=no_report_access_message, cta=False)
        modal_message = modal_messages.get_report_expenses_dialog(custom_message=no_report_access_message)

        # Update message in modal
        slack_client.views_update(user=user.slack_user_id, view=modal_message, view_id=modal_view_id)

        # Update notification message
        slack_client.chat_update(
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message,
            ts=private_metadata['notification_message_ts']
        )

    else:
        encoded_private_metadata = utils.encode_state(private_metadata)
        fetch_report_expenses(user=user, team_id=team_id, report=report, modal_view_id=modal_view_id, private_metadata=encoded_private_metadata)
        event_data = {
            'email': user.email,
            'slack_user_id': user.slack_user_id
        }

        tracking.identify_user(user.email)
        tracking.track_event(user.email, 'Report Expense Modal Opened', event_data)


def fetch_report_expenses(user: User, team_id: str, report: Dict, modal_view_id: str, private_metadata: str):
    slack_client = slack_utils.get_slack_client(team_id)

    fyle_report_approval = FyleReportApproval(user)
    query_params = {
        'report_id': 'eq.{}'.format(report['id']),
        'order': 'created_at.desc',
        'limit': '15',
        'offset': '0'
    }

    try:
        approver_report_expenses = fyle_report_approval.get_approver_report_expenses(query_params=query_params)
        report_expenses = approver_report_expenses['data']
    except exceptions.NotFoundItemError as error:
        logger.error('Report expenses not found with id -> %s', report['id'])
        logger.error('Error -> %s', error)
        # None here means report is deleted/doesn't exist
        report_expenses = None

    report_expenses_dialog = modal_messages.get_report_expenses_dialog(user=user, report=report, report_expenses=report_expenses, private_metadata=private_metadata)
    slack_client.views_update(user=user.slack_user_id, view=report_expenses_dialog, view_id=modal_view_id)
