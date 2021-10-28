from slack_sdk import WebClient

from django.conf import settings

from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.fyle.utils import get_fyle_oauth_url
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.models import Team, User, UserSubscriptionDetail
from fyle_slack_app.models.user_subscription_details import SubscriptionType
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.slack.utils import get_slack_client, get_slack_user_dm_channel_id
from fyle_slack_app.slack.ui.authorization import messages
from fyle_slack_app.slack.ui.dashboard import messages as dashboard_messages


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


def new_user_joined_pre_auth_message(user_id: str, team_id: str) -> None:
    # Check if the user has already authorized Fyle account
    # If already authorized, no need to send pre auth message
    user = utils.get_or_none(User, slack_user_id=user_id)

    if user is None:
        team = utils.get_or_none(Team, id=team_id)
        assertions.assert_found(team, 'Slack team not registered')

        slack_client = WebClient(token=team.bot_access_token)

        user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(user_info['ok'] is True)

        if user_info['user']['deleted'] is False and user_info['user']['is_bot'] is False:

            user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)

            fyle_oauth_url = get_fyle_oauth_url(user_id, team_id)

            pre_auth_message = messages.get_pre_authorization_message(user_info['user']['real_name'], fyle_oauth_url)

            slack_client.chat_postMessage(
                channel=user_dm_channel_id,
                blocks=pre_auth_message
            )


def uninstall_app(team_id: str) -> None:
    team = utils.get_or_none(Team, id=team_id)

    if team is not None:

        users = User.objects.filter(slack_team_id=team_id)

        # Disabling subscription for users in the team
        for user in users:
            access_token = fyle_utils.get_fyle_access_token(user.fyle_refresh_token)
            cluster_domain = fyle_utils.get_cluster_domain(access_token)

            fyle_profile = fyle_utils.get_fyle_profile(user.fyle_refresh_token)

            for subscription_type in SubscriptionType:
                subscription_webhook_details = SUBSCRIPTON_WEBHOOK_DETAILS_MAPPING[subscription_type]

                subscription_role_required = subscription_webhook_details['role_required']

                if subscription_role_required in fyle_profile['roles']:
                    fyle_user_id = user.fyle_user_id

                    subscription_detail = UserSubscriptionDetail.objects.get(
                        slack_user_id=user.slack_user_id,
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
                        logger.error('Error while disabling %s subscription for user: %s ', subscription_role_required, fyle_user_id)

        # Deleting team :)
        team.delete()


def handle_dashboard_view(user: User, team_id: str):

    slack_client = get_slack_client(team_id)

    fyle_expense = FyleExpense(user)

    unreported_expenses_query_params = {
        'offset': 0,
        'limit': 50,
        'order': 'created_at.desc',
        'and': '(state.eq.COMPLETE, report_id.is.null)'
    }

    unreported_expenses = fyle_expense.get_expenses(unreported_expenses_query_params)

    incomplete_expenses_query_params = {
        'offset': 0,
        'limit': 50,
        'order': 'created_at.desc',
        'state': 'eq.DRAFT'
    }

    incomplete_expenses = fyle_expense.get_expenses(incomplete_expenses_query_params)

    draft_reports_query_params = {
        'offset': 0,
        'limit': 50,
        'order': 'created_at.desc',
        'state': 'eq.DRAFT'
    }

    draft_reports = fyle_expense.get_reports(draft_reports_query_params)

    dashboard_view = dashboard_messages.get_post_authorization_message(team_id, unreported_expenses, incomplete_expenses, draft_reports)

    # Removing loading details section from view
    dashboard_view['blocks'] = dashboard_view['blocks'][:-1]

    slack_client.views_publish(user_id=user.slack_user_id, view=dashboard_view)
