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
                    "value": "enabled"
                },
                {
                    "text": {
                        "type": "plain_text",
                        "text": "Disable",
                        "emoji": True
                    },
                    "value": "disabled"
                }
            ],
            "action_id": "report_approval_notification_preference"
        }
	}
}


def get_notification_preferences_blocks(notification_types: List) -> List[Dict]:
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

    for notification_type in notification_types:
        notification_type_details = NOTIFICATION_TYPE_UI_DETAILS[notification_type]
        notification_preferences_blocks.append(notification_type_details)
        notification_preferences_blocks.append(
            {
			"type": "divider"
		    }
        )
    return notification_preferences_blocks
