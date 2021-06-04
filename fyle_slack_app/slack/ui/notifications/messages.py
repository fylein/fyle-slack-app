from typing import Dict, List

from fyle_slack_app.libs import utils


def get_report_section_blocks(title_text: str, report: Dict) -> List[Dict]:

    readable_submitted_at = utils.get_formatted_datetime(report['last_submitted_at'], '%B %d, %Y')

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
                        report['currency'],
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


def get_report_review_in_fyle_action(report_url: str, button_text: str, report_id: str) -> Dict:

    report_review_in_fyle_action = {
        'type': 'button',
        'text': {
            'type': 'plain_text',
            'text': button_text,
            'emoji': True
        },
        'action_id': 'review_report_in_fyle',
        'url': report_url,
        'value': report_id,
    }

    return report_review_in_fyle_action


def get_report_notification(report: Dict, report_url: str, title_text: str) -> List[Dict]:
    report_url = '{}/{}'.format(report_url, report['id'])
    report_query_params = {
        'org_id': report['org_id']
    }
    report_url = utils.convert_to_branchio_url(report_url, report_query_params)

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


def get_report_approval_state_section(report: Dict) -> Dict:
    report_approved_by = ''
    report_approval_pending_from = ''

    for approval in report['approvals']:
        approver_full_name = approval['approver_user']['full_name']
        approver_email = approval['approver_user']['email']

        if approval['state'] == 'APPROVAL_DONE':
            report_approved_by += '{} ({})\n'.format(approver_full_name, approver_email)

        if approval['state'] == 'APPROVAL_PENDING':
            report_approval_pending_from += '{} ({})\n'.format(approver_full_name, approver_email)

    report_approval_section = {
        'type': 'section',
        'fields': [
            {
                'type': 'mrkdwn',
                'text': '*Approved by:*\n {}'.format(report_approved_by)
            },
            {
                'type': 'mrkdwn',
                'text': '*Approval pending from:*\n {}'.format(report_approval_pending_from)
            }
        ]
    }

    return report_approval_section


def get_report_approved_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':white_check_mark: Your expense report <{}|[{}]> has been approved'.format(
                    report_url,
                    report['claim_number']
                )
    report_section_block = get_report_notification(report, report_url, title_text)

    report_approval_state_section = get_report_approval_state_section(report)

    report_section_block.insert(3, report_approval_state_section)

    return report_section_block


def get_report_payment_processing_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':moneybag: Payment is being processed for your expense report <{}|[{}]>'.format(
                    report_url,
                    report['claim_number']
                )

    report_section_block = get_report_notification(report, report_url, title_text)

    return report_section_block


def get_report_approver_sendback_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':bangbang: Your expense report <{}|[{}]> is sent back for changes'.format(
                    report_url,
                    report['claim_number']
                )

    report_section_block = get_report_notification(report, report_url, title_text)

    return report_section_block


def get_report_submitted_notification(report: Dict, report_url: str) -> List[Dict]:

    title_text = ':clipboard: Your expense report <{}|[{}]> has been submitted approval'.format(
                    report_url,
                    report['claim_number']
                )
    report_section_block = get_report_notification(report, report_url, title_text)

    report_approval_state_section = get_report_approval_state_section(report)

    report_section_block.insert(3, report_approval_state_section)

    return report_section_block


def get_report_approval_notification(report: Dict, user_display_name: str, report_url: str, message: str = None) -> List[Dict]:

    report_url = '{}/{}'.format(report_url, report['id'])
    report_query_params = {
        'org_id': report['org_id']
    }
    report_url = utils.convert_to_branchio_url(report_url, report_query_params)

    user_email = report['user']['email']

    report_claim_number = report['claim_number']

    title_text = ':envelope_with_arrow: *{}* ({}) submitted an expense report <{}|[{}]> for your approval'.format(
                    user_display_name,
                    user_email,
                    report_url,
                    report_claim_number
                )

    report_section_block = get_report_section_blocks(title_text, report)

    actions_block = {
        'type': 'actions',
        'elements': []
    }

    if message is not None:
        report_view_action_text = 'View in Fyle'
        message_section = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': message
            }
        }
        report_section_block.append(message_section)
    else:
        report_view_action_text = 'Review in Fyle'
        report_approve_action = {
            'type': 'button',
            'style': 'primary',
            'text': {
                'type': 'plain_text',
                'text': 'Approve',
                'emoji': True
            },
            'action_id': 'approve_report',
            'value': report['id'],
        }
        actions_block['elements'].append(report_approve_action)

    report_view_in_fyle_section = get_report_review_in_fyle_action(report_url, report_view_action_text, report['id'])

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
