from typing import Dict, List

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


def get_sent_back_reports_dashboard_view(reports: List[Dict]) -> List[Dict]:
	sent_back_reports_view = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": ":back: *Sent Back Reports - $ 231.45 (3)*"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "View all your sent back reports."
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": ":eyes: View in Fyle",
					},
					"value": "click_me_123",
					"action_id": "actionId-0"
				}
			]
		},
		{
			"type": "divider"
		}
	]
	return sent_back_reports_view


def get_incomplete_expenses_dashboard_view(reports: List[Dict]):
	incomplete_expenses_view = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": ":x: *Incompleted Expenses - $ 111.45 (7)*"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "View all your incomplete expenses."
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": ":eyes: View in Fyle",
					},
					"value": "click_me_123",
					"action_id": "actionId-0"
				}
			]
		},
		{
			"type": "divider"
		}
	]
	return incomplete_expenses_view


def get_unreported_expenses_dashboard_view(reports: List[Dict]):
	unreported_expenses_view = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": ":interrobang: *Unreported Expenses - $ 123.45 (12)*"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "View all your unreported expenses for approval."
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": ":eyes: View in Fyle",
					},
					"value": "click_me_123",
					"action_id": "actionId-0"
				}
			]
		},
		{
			"type": "divider"
		}
	]
	return unreported_expenses_view


def get_draft_reports_dashboard_view(reports: List[Dict]):
	draft_reports_view = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": ":open_file_folder: *Draft Reports - $ 2341.45 (7)*"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "View all your draft reports."
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": ":eyes: View in Fyle",
					},
					"value": "click_me_123",
					"action_id": "actionId-0"
				}
			]
		},
		{
			"type": "divider"
		}
	]
	return draft_reports_view


def get_dashboard_view(
	sent_back_reports: Dict,
	incomplete_expenses: Dict,
	unreported_expenses: Dict,
	draft_reports: Dict
) -> Dict:
	dashboard_view = {
		"type": "home",
		"blocks": [
			{
				"type": "section",
				"text": {
					"type": "mrkdwn",
					"text": "👋 *Hey there I'm Fyle Bot. Welcome to Fyle Dashboard!*"
				}
			},
			{
				"type": "section",
				"text": {
					"type": "mrkdwn",
					"text": "I can help you manage :receipt:  expenses and :envelope_with_arrow: reports, :rocket: approve reports if you're an approver and :zap: get instant notifications all here on Slack :slack:"
				}
			},
			{
				"type": "divider"
			},
		]
	}
	if sent_back_reports['count'] > 0:
		sent_back_reports_view = get_sent_back_reports_dashboard_view(sent_back_reports)
		dashboard_view['blocks'].extend(sent_back_reports_view)
	
	if incomplete_expenses['count'] > 0:
		incomplete_expenses_view = get_incomplete_expenses_dashboard_view(incomplete_expenses)
		dashboard_view['blocks'].extend(incomplete_expenses_view)

	if unreported_expenses['count'] > 0:
		unreported_expenses_view = get_unreported_expenses_dashboard_view(unreported_expenses)
		dashboard_view['blocks'].extend(unreported_expenses_view)
	
	if draft_reports['count'] > 0:
		draft_reports_view = get_draft_reports_dashboard_view(draft_reports)
		dashboard_view['blocks'].extend(draft_reports_view)

	return dashboard_view
