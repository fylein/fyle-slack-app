import base64

from slack_sdk import WebClient

from django.conf import settings
from django.db import transaction

from fyle_slack_app.fyle.utils import get_fyle_oauth_url
from fyle_slack_app.libs import utils, assertions, logger, http
from fyle_slack_app.models import Team, User, UserSubscriptionDetail
from fyle_slack_app.models.user_subscription_details import SubscriptionType
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.slack.utils import get_file_content_from_slack, get_slack_client, get_slack_user_dm_channel_id
from fyle_slack_app.slack.ui.authorization import messages


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
            cluster_domain = fyle_utils.get_cluster_domain(user.fyle_refresh_token)

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


def handle_file_shared(file_id: str, user_id: str, team_id: str):

    slack_client = get_slack_client(team_id)
    file_info =  slack_client.files_info(file=file_id)
    user = utils.get_or_none(User, slack_user_id=user_id)

    file_message_details = file_info['file']['shares']['private'][user.slack_dm_channel_id][0]
    file_url = file_info['file']['url_private']
    file_content = get_file_content_from_slack(file_url, user.slack_team.bot_access_token)
    encoded_file = base64.b64encode(file_content).decode('utf-8')

    # If thread_ts is present in message, this means file has been shared in a thread
    if 'thread_ts' in file_message_details:
        thread_ts = file_message_details['thread_ts']

        message_history = slack_client.conversations_history(channel=user.slack_dm_channel_id, latest=thread_ts, inclusive=True, limit=1)

        parent_message = message_history['messages'][0]

        # If a user upload a file which doesn't contain blocks, don't do anything
        if 'blocks' in parent_message:
            expense_block_id = parent_message['blocks'][0]['block_id']

            # If `expense_id` is present in message block id, this means user has uploaded the file to an expense thread
            # i.e. this file needs to be attached to an expense as a receipt
            if 'expense_id' in expense_block_id:
                _ , expense_id = expense_block_id.split('.')

                with transaction.atomic():
                    receipt_payload = {
                        'name': file_info['file']['name'],
                        'type': 'RECEIPT'
                    }
                    receipt = fyle_utils.create_receipt(receipt_payload, user.fyle_refresh_token)
                    receipt_urls = fyle_utils.generate_receipt_url(receipt['id'], user.fyle_refresh_token)
                    upload_file_response = fyle_utils.upload_file_to_s3(receipt_urls['upload_url'], file_content, receipt_urls['content_type'])
                    attach_receipt = fyle_utils.attach_receipt_to_expense(expense_id, receipt['id'], user.fyle_refresh_token)

    # This else block means file has been shared as a new message and an expense will be created with the file as receipt
    # i.e. data extraction flow
    else:
        print('DE FLOW')
        return None