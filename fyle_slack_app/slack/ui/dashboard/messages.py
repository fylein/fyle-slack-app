from typing import Dict

from fyle_slack_app.slack.ui.authorization import messages


def get_pre_authorization_message(user_name: str, fyle_oauth_url: str) -> Dict:
    pre_authorization_message_blocks = messages.get_pre_authorization_message(user_name, fyle_oauth_url)
    return {
        'type': 'home',
        'blocks': pre_authorization_message_blocks
    }


def get_post_authorization_message() -> Dict:
    post_authorization_message_blocks = messages.get_post_authorization_message()
    return {
        'type': 'home',
        'blocks': post_authorization_message_blocks
    }


def mock_message():
    return {
	"type": "modal",
	"title": {
		"type": "plain_text",
		"text": "My App",
		"emoji": True
	},
	"submit": {
		"type": "plain_text",
		"text": "Submit",
		"emoji": True
	},
	"close": {
		"type": "plain_text",
		"text": "Cancel",
		"emoji": True
	},
	"blocks": [
		{
            "dispatch_action": True,
			"type": "input",
			"element": {
				"type": "external_select",
				"placeholder": {
					"type": "plain_text",
					"text": "Select an item",
					"emoji": True
				},
				"action_id": "external_select_option"
			},
			"label": {
				"type": "plain_text",
				"text": "Label",
				"emoji": True
			}
		}
	]
}


def mock_message_2():
    return {
	"type": "modal",
	"title": {
		"type": "plain_text",
		"text": "My App",
		"emoji": True
	},
	"submit": {
		"type": "plain_text",
		"text": "Submit",
		"emoji": True
	},
	"close": {
		"type": "plain_text",
		"text": "Cancel",
		"emoji": True
	},
	"blocks": [
		{
            "dispatch_action": True,
			"type": "input",
			"element": {
				"type": "external_select",
				"placeholder": {
					"type": "plain_text",
					"text": "Select an item",
					"emoji": True
				},
				"action_id": "external_select_option"
			},
			"label": {
				"type": "plain_text",
				"text": "Label",
				"emoji": True
			}
		},
		{
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": "Dynamic updated view",
				"emoji": True
			}
		}
	]
}