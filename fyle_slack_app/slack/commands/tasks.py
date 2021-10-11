from django.conf import settings

from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.models import User, UserSubscriptionDetail
from fyle_slack_app.models.user_subscription_details import SubscriptionType
from fyle_slack_app.slack.commands.handlers import SlackCommandHandler
from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.slack.ui.expenses import messages as expense_messages


logger = logger.get_logger(__name__)


SUBSCRIPTON_WEBHOOK_DETAILS_MAPPING = {
    SubscriptionType.FYLER_SUBSCRIPTION: {
        'role_required': 'FYLER',
        'webhook_url': '{}/fyle/fyler/notifications'.format(settings.SLACK_SERVICE_BASE_URL)
    },
    SubscriptionType.APPROVER_SUBSCRIPTION: {
        'role_required': 'APPROVER',
        'webhook_url': '{}/fyle/approver/notifications'.format(settings.SLACK_SERVICE_BASE_URL)
    }
}


def fyle_unlink_account(user_id: str, team_id: str, user_dm_channel_id: str) -> None:
    user = utils.get_or_none(User, slack_user_id=user_id)

    slack_client = slack_utils.get_slack_client(team_id)

    # Text message if user hasn't linked Fyle account
    text = 'Hey buddy, you haven\'t linked your Fyle account yet :face_with_head_bandage: \n' \
        'Checkout home tab for `Link Your Fyle Account` to link your Slack with Fyle :zap:'

    if user is not None:
        is_error_occured = False

        # Disabling user subscription
        access_token = fyle_utils.get_fyle_access_token(user.fyle_refresh_token)
        cluster_domain = fyle_utils.get_cluster_domain(access_token)

        fyle_profile = fyle_utils.get_fyle_profile(user.fyle_refresh_token)

        for subscription_type in SubscriptionType:
            subscription_webhook_details = SUBSCRIPTON_WEBHOOK_DETAILS_MAPPING[subscription_type]

            subscription_role_required = subscription_webhook_details['role_required']

            if subscription_role_required in fyle_profile['roles']:
                fyle_user_id = user.fyle_user_id

                subscription_detail = UserSubscriptionDetail.objects.get(
                    slack_user_id=user_id,
                    subscription_type=subscription_type.value
                )

                webhook_url = subscription_webhook_details['webhook_url']
                webhook_url = '{}/{}'.format(webhook_url, subscription_detail.webhook_id)

                subscription_payload = {}
                subscription_payload['data'] = {
                    'id': subscription_detail.subscription_id,
                    'webhook_url': webhook_url,
                    'is_enabled': False
                }

                subscription = fyle_utils.upsert_fyle_subscription(cluster_domain, access_token, subscription_payload, subscription_type)

                if subscription.status_code != 200:
                    text = 'Looks like something went wrong :zipper_mouth_face: \n Please try again'
                    is_error_occured = True

                    logger.error('Error while disabling %s subscription for user: %s ', subscription_role_required, fyle_user_id)
                    assertions.assert_good(False)

        # Deleting user entry to unlink fyle account
        if is_error_occured is False:
            user.delete()
            text = 'Hey, you\'ve successfully unlinked your Fyle account with slack :white_check_mark:\n ' \
            'If you change your mind about us checkout home tab for `Link Your Fyle Account` to link your Slack with Fyle :zap:'

        # Update home tab with pre auth message
        SlackCommandHandler().update_home_tab_with_pre_auth_message(user_id, team_id)

        # Track Fyle account unlinked
        SlackCommandHandler().track_fyle_account_unlinked(user)

    slack_client.chat_postMessage(
        channel=user_dm_channel_id,
        text=text
    )


def open_expense_form(user: User, team_id: str, view_id: str) -> None:

    fyle_expense = FyleExpense(user)

    default_expense_fields = fyle_expense.get_default_expense_fields()

    slack_client = slack_utils.get_slack_client(team_id)

    fyle_profile = fyle_utils.get_fyle_profile(user.fyle_refresh_token)

    home_currency = fyle_profile['org']['currency']

    field_type_mandatory_mapping = fyle_expense.get_expense_fields_type_mandatory_mapping(default_expense_fields)

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

    # Create a expense fields render property and set them optional in the form
    fields_render_property = {
        'project': is_project_available,
        'cost_center': is_cost_centers_available,
        'purpose': field_type_mandatory_mapping['purpose'],
        'transaction_date': field_type_mandatory_mapping['txn_dt'],
        'vendor': field_type_mandatory_mapping['vendor_id']
    }

    additional_currency_details = {
        'home_currency': home_currency
    }

    add_to_report = 'existing_report'

    # Caching details in slack private metadata so that they can be reused again in the form without computing them again
    private_metadata = {
        'fields_render_property': fields_render_property,
        'home_currency': home_currency,
        'additional_currency_details': additional_currency_details,
        'add_to_report': add_to_report
    }

    encoded_metadata = utils.encode_state(private_metadata)

    expense_form = expense_messages.expense_dialog_form(fields_render_property=fields_render_property, private_metadata=encoded_metadata, additional_currency_details=additional_currency_details, add_to_report=add_to_report)

    slack_client.views_update(view=expense_form, view_id=view_id)
