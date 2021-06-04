from typing import Dict, List

from fyle_slack_app.models.notification_preferences import NotificationType


NOTIFICATION_TYPE_UI_DETAILS = {
    NotificationType.REPORT_SUBMITTED.value: {
        'role_required': 'APPROVER',
        'ui': {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*Report submitted for approval :envelope_with_arrow: * \n _Get notified when an expense report gets submitted for your approval_'
            },
            'accessory': {
                'type': 'radio_buttons',
                'action_id': 'report_submitted_notification_preference'
            }
        }
    },
    NotificationType.REPORT_PARTIALLY_APPROVED.value: {
        'role_required': 'FYLER',
        'ui': {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*Report approved :white_check_mark: * \n_Get notified when your expense report gets approved_'
            },
            'accessory': {
                'type': 'radio_buttons',
                'action_id': 'report_partially_approved_notification_preference'
            }
        }
    },
    NotificationType.REPORT_APPROVER_SENDBACK.value: {
        'role_required': 'FYLER',
        'ui': {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*Report sent back for inquiry :bangbang: * \n_Get notified when your expense report is sent back for inquiry_'
            },
            'accessory': {
                'type': 'radio_buttons',
                'action_id': 'report_approver_sendback_notification_preference'
            }
        }
    },
    NotificationType.REPORT_PAYMENT_PROCESSING.value: {
        'role_required': 'FYLER',
        'ui': {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*Payment processing :moneybag: * \n_Get notified when payment is being processed for your expense report_'
            },
            'accessory': {
                'type': 'radio_buttons',
                'action_id': 'report_payment_processing_notification_preference'
            }
        }
    }
}


def get_notification_preference_option(is_enabled: bool) -> Dict:
    option_text, option_value = ('Enable', 'enable') if is_enabled is True else ('Disable', 'disable')

    option = {
        'text': {
            'type': 'plain_text',
            'text': option_text,
            'emoji': True
        },
        'value': option_value
    }

    return option


def check_notification_roles_allowed(role_required: str, user_roles: List[str]) -> bool:
    allowed = False

    if role_required in user_roles:
        allowed = True

    return allowed


def get_notification_preferences_blocks(notification_preferences: List[Dict], fyle_roles: List[str]) -> List[Dict]:
    notification_preferences_blocks = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*Notification Preferences :bell:*'
            }
        },
        {
            'type': 'divider'
        }
    ]

    for notification_preference in notification_preferences:

        notification_type_details = NOTIFICATION_TYPE_UI_DETAILS.get(notification_preference['notification_type'])

        if notification_type_details is not None:

            notification_type_role_required = notification_type_details['role_required']

            is_notification_type_allowed = check_notification_roles_allowed(notification_type_role_required, fyle_roles)

            if is_notification_type_allowed is True:

                notification_type_ui = notification_type_details['ui']

                notification_type_ui['accessory']['options'] = []
                enabled_notification_preference_option = get_notification_preference_option(True)
                disabled_notification_preference_option = get_notification_preference_option(False)

                notification_type_ui['accessory']['options'].append(enabled_notification_preference_option)
                notification_type_ui['accessory']['options'].append(disabled_notification_preference_option)

                notification_preference_initial_option = get_notification_preference_option(notification_preference['is_enabled'])
                notification_type_ui['accessory']['initial_option'] = notification_preference_initial_option

                notification_preferences_blocks.append(notification_type_ui)

                notification_preferences_blocks.append(
                    {
                    'type': 'divider'
                    }
                )
    return notification_preferences_blocks
