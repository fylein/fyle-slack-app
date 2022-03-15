from typing import Dict, List

from fyle_slack_app.libs import utils
from fyle_slack_app.slack import utils as slack_utils


def get_report_section_blocks(title_text: str, report: Dict) -> List[Dict]:

    readable_submitted_at = utils.get_formatted_datetime(report['last_submitted_at'], '%B %d, %Y')
    report_currency_symbol = slack_utils.get_currency_symbol(report['currency'])

    report_section_block = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': title_text
            }
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Report name:*\n {}'.format(report['purpose'])
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Number of expenses:*\n {}'.format(report['num_expenses'])
                }
            ]
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Amount:*\n {} {}'.format(
                        report_currency_symbol,
                        report['amount']
                    )
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Submitted on:*\n {}'.format(readable_submitted_at)
                }
            ]
        }
    ]

    return report_section_block


def get_expense_section_blocks(title_text: str, expense: Dict) -> List[Dict]:

    category = expense['category']['name']
    sub_category = expense['category']['sub_category']

    if sub_category is not None and category != sub_category:
        category = '{} / {}'.format(category, sub_category)

    currency_symbol = slack_utils.get_currency_sysmbol(expense['currency'])
    amount = expense['amount']

    amount_details = '*Amount:*\n {} {}'.format(currency_symbol, amount)

    # If foreign currency exists, then show foreign amount and currency
    if expense['foreign_currency'] is not None:
        foreign_currency_symbol = slack_utils.get_currency_sysmbol(expense['foreign_currency'])
        foreign_amount = expense['foreign_amount']

        amount_details = '{} \n ({} {})'.format(amount_details, foreign_currency_symbol, foreign_amount)

    expense_section_block = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': title_text
            }
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': amount_details
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Category:*\n {}'.format(category)
                }
            ]
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Merchant:*\n {}'.format(
                        expense['merchant']
                    )
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Purpose:*\n {}'.format(expense['purpose'])
                }
            ]
        }
    ]

    project = expense['project']

    if project is not None:
        project = expense['project']['name']
        sub_project = expense['project']['sub_project']

        if sub_project is not None:
            project = '{} / {}'.format(project, sub_project)

        project_section = {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Project:*\n {}'.format(
                        project
                    )
                }
            ]
        }

        expense_section_block.append(project_section)

    return expense_section_block


def get_report_review_in_slack_action(button_text: str, report_id: str) -> Dict:
    report_review_in_slack_action = {
        'type': 'button',
        'style': 'primary',
        'text': {
            'type': 'plain_text',
            'text': ':slack: {}'.format(button_text),
            'emoji': True
        },
        'value': report_id,
        'action_id': 'open_report_expenses_dialog'
    }

    return report_review_in_slack_action


def get_report_review_in_fyle_action(report_url: str, button_text: str, report_id: str) -> Dict:

    report_review_in_fyle_action = {
        'type': 'button',
        'text': {
            'type': 'plain_text',
            'text': ':eyes: {}'.format(button_text),
            'emoji': True
        },
        'action_id': 'review_report_in_fyle',
        'url': report_url,
        'value': report_id,
    }

    return report_review_in_fyle_action


def get_expense_view_in_fyle_action(expense_url: str, button_text: str, expense_id: str) -> Dict:

    expense_view_in_fyle_action = {
        'type': 'button',
        'text': {
            'type': 'plain_text',
            'text': button_text,
            'emoji': True
        },
        'action_id': 'expense_view_in_fyle',
        'url': expense_url,
        'value': expense_id,
    }

    return expense_view_in_fyle_action


def get_report_notification(report: Dict, report_url: str, title_text: str) -> List[Dict]:

    report_section_block = get_report_section_blocks(title_text, report)

    actions_block = {
        'type': 'actions',
        'elements': []
    }

    report_view_in_fyle_section = get_report_review_in_fyle_action(report_url, 'View in Fyle', report['id'])

    actions_block['elements'].append(report_view_in_fyle_section)
    report_section_block.append(actions_block)

    # Adding Notification Preference message as footer
    report_section_block.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Check *Fyle Notification Preferences* in quick actions :zap: to customise notifications you receive from Fyle"
                }
            ]
        }
    )

    return report_section_block


def get_expense_notification(expense: Dict, expense_url: str, title_text: str) -> List[Dict]:

    expense_section_block = get_expense_section_blocks(title_text, expense)

    actions_block = {
        'type': 'actions',
        'elements': []
    }

    expense_view_in_fyle_section = get_expense_view_in_fyle_action(expense_url, 'View in Fyle', expense['id'])

    actions_block['elements'].append(expense_view_in_fyle_section)
    expense_section_block.append(actions_block)

    # Adding Notification Preference message as footer
    expense_section_block.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Check *Fyle Notification Preferences* in quick actions :zap: to customise notifications you receive from Fyle"
                }
            ]
        }
    )

    return expense_section_block


def get_report_approval_state_section(report: Dict) -> Dict:
    report_approved_by = ''
    report_approval_pending_from = ''
    is_report_fully_approved = True

    for approval in report['approvals']:
        approver_full_name = approval['approver_user']['full_name']
        approver_email = approval['approver_user']['email']

        if approval['state'] == 'APPROVAL_DONE':
            report_approved_by += '{} ({})\n'.format(approver_full_name, approver_email)

        if approval['state'] == 'APPROVAL_PENDING':
            report_approval_pending_from += '{} ({})\n'.format(approver_full_name, approver_email)
            is_report_fully_approved = False

    report_approval_section = {
        'type': 'section',
        'fields': [
            {
                'type': 'mrkdwn',
                'text': '*Approved by:*\n {}'.format(report_approved_by)
            }
        ]
    }

    if is_report_fully_approved is False:
        report_approval_section['fields'].append(
            {
                'type': 'mrkdwn',
                'text': '*Approval pending from:*\n {}'.format(report_approval_pending_from)
            }
        )

    return report_approval_section


def get_report_approved_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':white_check_mark: Your expense report <{}|[{}]> has been approved'.format(
        report_url,
        report['seq_num']
    )
    report_section_block = get_report_notification(report, report_url, title_text)

    report_approval_state_section = get_report_approval_state_section(report)

    report_section_block.insert(3, report_approval_state_section)

    return report_section_block, title_text


def get_report_payment_processing_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':moneybag: Payment is being processed for your expense report <{}|[{}]>'.format(
        report_url,
        report['seq_num']
    )

    report_section_block = get_report_notification(report, report_url, title_text)

    return report_section_block, title_text


def get_report_paid_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':dollar: Reimbursement for your expense report <{}|[{}]> is here!'.format(
        report_url,
        report['seq_num']
    )

    report_section_block = get_report_notification(report, report_url, title_text)

    return report_section_block, title_text


def get_report_approver_sendback_notification(report: Dict, report_url: str, report_sendback_reason: str) -> List[Dict]:

    title_text = ':bangbang: *{}* ({}) sent back your expense report <{}|[{}]> '.format(
        report['updated_by_user']['full_name'],
        report['updated_by_user']['email'],
        report_url,
        report['seq_num']
    )

    report_section_block = get_report_notification(report, report_url, title_text)

    report_sendback_reason = report_sendback_reason.replace('reason for sending back report: ', '')

    report_sendback_reason_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ">>>*Reason for sending back report:* \n {}".format(
                report_sendback_reason,
            )
        }
    }

    report_section_block.insert(1, report_sendback_reason_section)

    return report_section_block, title_text


def get_report_submitted_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':clipboard: Your expense report <{}|[{}]> has been submitted for approval'.format(
        report_url,
        report['seq_num']
    )
    report_section_block = get_report_notification(report, report_url, title_text)

    report_approval_state_section = get_report_approval_state_section(report)

    report_section_block.insert(3, report_approval_state_section)

    return report_section_block, title_text


def get_report_approval_notification(report: Dict, user_display_name: str, report_url: str, message: str = None) -> List[Dict]:

    user_email = report['user']['email']

    report_seq_num = report['seq_num']

    title_text = ':envelope_with_arrow: *{}* ({}) submitted an expense report <{}|[{}]> for your approval'.format(
        user_display_name,
        user_email,
        report_url,
        report_seq_num
    )

    report_section_block = get_report_section_blocks(title_text, report)

    actions_block = {
        'type': 'actions',
        'elements': []
    }

    if message is not None:
        report_view_in_fyle_action_text = 'View in Fyle'
        message_section = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': message
            }
        }
        report_section_block.append(message_section)
    else:
        report_view_in_fyle_action_text = 'Review in Fyle'

        report_approve_action = {
            'type': 'button',
            'style': 'primary',
            'text': {
                'type': 'plain_text',
                'text': ':rocket: Approve',
                'emoji': True
            },
            'action_id': 'approve_report',
            'value': report['id'],
        }
        actions_block['elements'].append(report_approve_action)

        # Adding "Review in Slack" button to the message block
        report_view_in_slack_action_text = 'Review in Slack'
        report_view_in_slack_section = get_report_review_in_slack_action(report_view_in_slack_action_text, report['id'])
        actions_block['elements'].append(report_view_in_slack_section)

    report_view_in_fyle_section = get_report_review_in_fyle_action(report_url, report_view_in_fyle_action_text, report['id'])
    actions_block['elements'].append(report_view_in_fyle_section)

    report_section_block.append(actions_block)

    # Adding Notification Preference message as footer
    report_section_block.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Check *Fyle Notification Preferences* in quick actions :zap: to customise notifications you receive from Fyle"
                }
            ]
        }
    )

    return report_section_block, title_text


def get_report_commented_notification(report: Dict, user_display_name: str, report_url: str, report_comment: str) -> List[Dict]:

    title_text = ':speech_balloon:  *{}* ({}) commented on your expense report <{}|[{}]> '.format(
        user_display_name,
        report['updated_by_user']['email'],
        report_url,
        report['seq_num']
    )

    report_section_block = get_report_notification(report, report_url, title_text)

    report_comment_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ">>>\"{}\"  - *{}*".format(
                report_comment,
                report['updated_by_user']['full_name']
            )
        }
    }

    report_section_block.insert(1, report_comment_block)

    return report_section_block, title_text


def get_expense_commented_notification(expense: Dict, user_display_name: str, expense_url: str, expense_comment: str) -> List[Dict]:

    title_text = ':speech_balloon:  *{}* ({}) commented on your expense <{}|[{}]> '.format(
        user_display_name,
        expense['updated_by_user']['email'],
        expense_url,
        expense['seq_num']
    )

    expense_section_block = get_expense_notification(expense, expense_url, title_text)

    expense_comment_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ">>>\"{}\"  - *{}*".format(
                expense_comment,
                expense['updated_by_user']['full_name']
            )
        }
    }

    expense_section_block.insert(1, expense_comment_block)

    return expense_section_block, title_text
