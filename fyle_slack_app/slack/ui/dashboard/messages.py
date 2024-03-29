from typing import Dict, List

from fyle_slack_app.slack.ui.authorization import messages
from fyle_slack_app.slack.utils import get_display_amount


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


def get_sent_back_reports_dashboard_view(reports: Dict, home_currency: str) -> List[Dict]:
    display_amount = get_display_amount(reports['total_amount'], home_currency)

    sent_back_reports_view = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":back: *Sent Back Reports - {} ({})*".format(display_amount, reports['count'])
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
                    "url": reports['url'],
                    "action_id": "sent_back_reports_viewed_in_fyle",
                    "value": 'Sent Back Reports Viewed In Fyle'
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    return sent_back_reports_view


def get_incomplete_expenses_dashboard_view(expenses: Dict, home_currency: str):
    display_amount = get_display_amount(expenses['total_amount'], home_currency)

    incomplete_expenses_view = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":x: *Incomplete Expenses - {} ({})*".format(display_amount, expenses['count'])
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
                    "url": expenses['url'],
                    "action_id": "incomplete_expenses_viewed_in_fyle",
                    "value": 'Incomplete Expenses Viewed In Fyle'
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    return incomplete_expenses_view


def get_unreported_expenses_dashboard_view(expenses: Dict, home_currency: str):
    display_amount = get_display_amount(expenses['total_amount'], home_currency)

    unreported_expenses_view = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":interrobang: *Complete Expenses - {} ({})*".format(display_amount, expenses['count'])
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "View all your complete expenses for approval."
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
                    "url": expenses['url'],
                    "action_id": "unreported_expenses_viewed_in_fyle",
                    "value": 'Complete Expenses Viewed In Fyle'
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    return unreported_expenses_view


def get_draft_reports_dashboard_view(reports: Dict, home_currency: str):
    display_amount = get_display_amount(reports['total_amount'], home_currency)

    draft_reports_view = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":open_file_folder: *Draft Reports - {} ({})*".format(display_amount, reports['count'])
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
                    "url": reports["url"],
                    "action_id": "draft_reports_viewed_in_fyle",
                    "value": 'Draft Reports Viewed In Fyle'
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
    draft_reports: Dict,
    home_currency: str,
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
    if sent_back_reports is not None:
        sent_back_reports_view = get_sent_back_reports_dashboard_view(sent_back_reports, home_currency)
        dashboard_view['blocks'].extend(sent_back_reports_view)

    if incomplete_expenses is not None:
        incomplete_expenses_view = get_incomplete_expenses_dashboard_view(incomplete_expenses, home_currency)
        dashboard_view['blocks'].extend(incomplete_expenses_view)

    if unreported_expenses is not None:
        unreported_expenses_view = get_unreported_expenses_dashboard_view(unreported_expenses, home_currency)
        dashboard_view['blocks'].extend(unreported_expenses_view)

    if draft_reports is not None:
        draft_reports_view = get_draft_reports_dashboard_view(draft_reports, home_currency)
        dashboard_view['blocks'].extend(draft_reports_view)

    return dashboard_view
