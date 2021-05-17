from typing import Dict, List

from fyle_slack_app.models.notification_preferences import NotificationType


NOTIFICATION_TYPE_UI_DETAILS = {
    NotificationType.APPROVER_REPORT_APPROVAL.value: {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Report submitted for approval :envelope_with_arrow: * \n _Get notified when an expense report gets submitted for your approval_"
        },
        "accessory": {
            "type": "radio_buttons",
            "options": [
                {
                    "text": {
                        "type": "plain_text",
                        "text": "Enable",
                        "emoji": True
                    },
                    "value": "enable"
                },
                {
                    "text": {
                        "type": "plain_text",
                        "text": "Disable",
                        "emoji": True
                    },
                    "value": "disable"
                }
            ],
            "action_id": "approver_report_approval_notification_preference"
        }
	}
}


def get_notification_preference_option(is_enabled: bool) -> Dict:
    option_text = 'Disable'
    option_value = 'disable'

    if is_enabled:
        option_text = 'Enable'
        option_value = 'enable'

    option = {
        "text": {
            "type": "plain_text",
            "text": option_text,
            "emoji": True
        },
        "value": option_value
    }

    return option


def get_notification_preferences_blocks(notification_preferences: List[Dict]) -> List[Dict]:
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

        notification_preference_initial_option = get_notification_preference_option(notification_preference['is_enabled'])
        notification_type_details['accessory']['initial_option'] = notification_preference_initial_option

        notification_preferences_blocks.append(notification_type_details)

        notification_preferences_blocks.append(
            {
			"type": "divider"
		    }
        )
    return notification_preferences_blocks
