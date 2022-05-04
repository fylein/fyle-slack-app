from typing import Dict
from slack_sdk import WebClient

from django.conf import settings

from fyle_slack_app.fyle.expenses.views import FyleExpense

from fyle_slack_app.fyle.utils import get_fyle_oauth_url
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.models import Team, User, UserSubscriptionDetail
from fyle_slack_app.models.user_subscription_details import SubscriptionType
from fyle_slack_app.fyle import utils as fyle_utils

from fyle_slack_app.slack.interactives.block_action_handlers import BlockActionHandler
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.ui.authorization import messages
from fyle_slack_app.slack.ui import common_messages


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

            user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)

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
    slack_client = slack_utils.get_slack_client(team_id)
    user = utils.get_or_none(User, slack_user_id=user_id)

    file_info = slack_client.files_info(file=file_id)
    file_message_details = file_info['file']['shares']['private'][user.slack_dm_channel_id][0]
    file_url = file_info['file']['url_private']
    file_content = slack_utils.get_file_content_from_slack(file_url, user.slack_team.bot_access_token)

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

                # Check if file is supported or not
                is_file_supported, file_response_message = fyle_utils.is_receipt_file_supported(file_info)

                if is_file_supported is not True:
                    # If file not supported, notify user in the same slack thread
                    file_not_supported_message_block = common_messages.get_custom_text_section_block(file_response_message)
                    slack_client.chat_postMessage(
                        channel=user.slack_dm_channel_id,
                        blocks=file_not_supported_message_block,
                        thread_ts=thread_ts
                    )

                else:
                    _ , expense_id = expense_block_id.split('.')

                    expense = FyleExpense(user).get_expense_by_id(expense_id)

                    if expense is None:
                        # Case when expense has been deleted or user has no longer access to it

                        logger.error('Expense not found with id -> %s', expense_id)

                        no_access_message = 'Looks like you no longer have access to this expense :face_with_head_bandage:'
                        no_access_message_block = common_messages.get_custom_text_section_block(no_access_message)

                        # Post message in slack thread
                        slack_client.chat_postMessage(
                            channel=user.slack_dm_channel_id,
                            blocks=no_access_message_block,
                            thread_ts=thread_ts
                        )

                        # Update parent message
                        parent_message_blocks = parent_message['blocks']
                        parent_message_ts = parent_message['ts']
                        parent_message_blocks[-1] = no_access_message_block[0]

                        slack_client.chat_update(
                            blocks=parent_message_blocks,
                            ts=parent_message_ts,
                            channel=user.slack_dm_channel_id
                        )

                    else:
                        receipt_uploading_message = ':mag: Uploading receipt.... Your receipt will be attached shortly!'
                        receipt_uploading_message_block = common_messages.get_custom_text_section_block(receipt_uploading_message)

                        response = slack_client.chat_postMessage(
                            channel=user.slack_dm_channel_id,
                            blocks=receipt_uploading_message_block,
                            thread_ts=thread_ts
                        )
                        message_ts = response['message']['ts']

                        # Handle creation of receipt file urls, uploading to s3, and attaching receipt to the expense
                        handle_upload_and_attach_receipt(slack_client, user, file_info, file_content, expense_id, parent_message, message_ts, thread_ts)

    # This else block means file has been shared as a new message and an expense will be created with the file as receipt
    # i.e. data extraction flow
    else:
        return None


def handle_upload_and_attach_receipt(slack_client: WebClient, user: User, file_info: Dict, file_content: str, expense_id: str, parent_message: Dict, message_ts: str, thread_ts: str):
    receipt_payload = {
        'name': file_info['file']['name'],
        'type': 'RECEIPT'
    }

    try:
        receipt = fyle_utils.create_receipt(receipt_payload, user.fyle_refresh_token)
        receipt_urls = fyle_utils.generate_receipt_url(receipt['id'], user.fyle_refresh_token)
        fyle_utils.upload_file_to_s3(receipt_urls['upload_url'], file_content, receipt_urls['content_type'])
        attached_receipt = fyle_utils.attach_receipt_to_expense(expense_id, receipt['id'], user.fyle_refresh_token)

    except assertions.InvalidUsage as error:
        logger.error('Unable to attach receipt to expense with id -> %s', expense_id)
        logger.error('Error -> %s', error)
        attached_receipt = None

    if attached_receipt is not None:
        # Update the message in slack thread
        receipt_uploaded_success_message = ':receipt: Receipt for this expense has been successfully attached :white_check_mark:'
        receipt_uploaded_success_message_block = common_messages.get_custom_text_section_block(receipt_uploaded_success_message)
        slack_client.chat_update(
            channel=user.slack_dm_channel_id,
            blocks=receipt_uploaded_success_message_block,
            ts=message_ts,
            thread_ts=thread_ts
        )

        # Update the parent message accordingly
        parent_message_blocks = parent_message['blocks']
        parent_message_blocks[1]['fields'][1]['text'] = 'Receipt:\n :white_check_mark: *Attached*'
        parent_message_ts = parent_message['ts']

        # Hide the 'Attach Receipt' button after receipt has been attached
        if len(parent_message_blocks[3]['elements']) > 1:
            del parent_message_blocks[3]['elements'][0]

        slack_client.chat_update(
            channel=user.slack_dm_channel_id,
            blocks=parent_message_blocks,
            ts=parent_message_ts
        )

        event_data = {
            'slack_user_id': user.slack_user_id,
            'team_id': user.slack_team_id,
            'expense_id': expense_id,
            'email': user.email,
            'fyle_org_id': user.fyle_org_id,
            'fyle_user_id': user.fyle_user_id
        }
        BlockActionHandler().track_view_in_fyle_action(user.slack_user_id, 'Receipt attached from Slack', event_data)

    else:
        error_message = 'Looks like something went wrong :zipper_mouth_face: \n Please try again'
        error_message_block = common_messages.get_custom_text_section_block(error_message)
        slack_client.chat_update(
            channel=user.slack_dm_channel_id,
            blocks=error_message_block,
            ts=message_ts,
            thread_ts=thread_ts
        )
