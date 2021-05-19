from typing import Dict, List

from fyle_slack_app.models.notification_preferences import NotificationType


NOTIFICATION_TYPE_UI_DETAILS = {
    NotificationType.APPROVER_REPORT_APPROVAL.value: {
        'role_required': 'APPROVER',
        'ui': {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Report submitted for approval :envelope_with_arrow: * \n _Get notified when an expense report gets submitted for your approval_"
            },
            "accessory": {
                "type": "radio_buttons",
                "action_id": "approver_report_approval_notification_preference"
            }
        }
    }
}


def get_notification_preference_option(is_enabled: bool) -> Dict:
    option_text, option_value = ('Enable', 'enable') if is_enabled is True else ('Disable', 'disable')

    option = {
        "text": {
            "type": "plain_text",
            "text": option_text,
            "emoji": True
        },
        "value": option_value
    }

    return option


def check_notification_roles_allowed(role_required, user_roles):
    allowed = False

    if role_required in user_roles:
        allowed = True

    return allowed


def get_notification_preferences_blocks(notification_preferences: List[Dict], fyle_roles: List[str]) -> List[Dict]:
    notification_preferences_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Notification Preferences :bell:*"
            }
        },
        {
            "type": "divider"
        }
    ]

    for notification_preference in notification_preferences:

        notification_type_details = NOTIFICATION_TYPE_UI_DETAILS[notification_preference['notification_type']]

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
                "type": "divider"
                }
            )
    return notification_preferences_blocks
