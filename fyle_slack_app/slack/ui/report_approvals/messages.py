from typing import Dict, List

from fyle_slack_app.libs import utils


def get_report_section_blocks(report: Dict, user_display_name: str) -> List[Dict]:

    readable_submitted_at = utils.get_formatted_datetime(report['last_submitted_at'], '%B %d, %Y')

    user_email = report['user']['email']

    report_claim_number = report['claim_number']
    report_curreny = report['currency']
    report_amount = report['amount']
    report_expenses = report['num_expenses']

    report_section_block = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':envelope_with_arrow: *{}* ( {} ) submitted an expense report [ {} ] for your approval'.format(
                    user_display_name,
                    user_email,
                    report_claim_number
                )
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*{}*'.format(report['purpose'])
            }
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Amount:* {} {} \n *No. of expenses:* {}'.format(
                        report_curreny,
                        report_amount,
                        report_expenses
                    )
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Submitted On:* {}'.format(readable_submitted_at)
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


def get_report_approval_notification(report: Dict, user_display_name: str, report_url: str, message: str = None) -> List[Dict]:

    report_url = '{}/{}'.format(report_url, report['id'])
    report_query_params = {
        'org_id': report['org_id']
    }
    report_url = utils.convert_to_branchio_url(report_url, report_query_params)

    report_section_block = get_report_section_blocks(report, user_display_name)

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

    return report_section_block
