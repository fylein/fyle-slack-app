import datetime


def get_report_section_blocks(report, employee_display_name):

    submitted_at = datetime.datetime.fromisoformat(report['submitted_at'])
    readable_submitted_at = submitted_at.strftime('%B %d, %Y')

    return [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*{}* ( {} ) submitted an expense report [ {} ] for your approval'.format(
                    employee_display_name,
                    report['employee']['user']['email'],
                    report['claim_number']
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
                        report['currency'],
                        report['amount'],
                        report['num_expenses']
                    )
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Submitted On:* {}'.format(readable_submitted_at)
                }
            ]
        }
    ]


def get_report_review_in_fyle_action(report_url, button_text):
    return {
        'type': 'button',
        'text': {
            'type': 'plain_text',
            'text': button_text,
            'emoji': True
        },
        'action_id': 'report_review_in_fyle',
        'url': report_url
    }


def get_report_approval_notification_message(report, employee_display_name, report_url, message=None):

    report_url = '{}/{}?org_id={}'.format(report_url, report['id'], report['org_id'])

    report_section_block = get_report_section_blocks(report, employee_display_name)

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
            'action_id': 'report_approve',
            'value': report['id'],
        }
        actions_block['elements'].append(report_approve_action)

    report_view_in_fyle_section = get_report_review_in_fyle_action(report_url, report_view_action_text)

    actions_block['elements'].append(report_view_in_fyle_section)
    report_section_block.append(actions_block)

    return report_section_block
