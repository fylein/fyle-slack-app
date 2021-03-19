from ....libs import utils


def get_report_section_blocks(report, employee_display_name):

    readable_submitted_at = utils.get_formatted_datetime(report['submitted_at'], '%B %d, %Y')

    employee_email = report['employee']['user']['email']

    report_claim_number = report['claim_number']
    report_curreny = report['currency']
    report_amount = report['amount']
    report_expenses = report['num_expenses']

    report_section_block = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*{}* ( {} ) submitted an expense report [ {} ] for your approval'.format(
                    employee_display_name,
                    employee_email,
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


def get_report_review_in_fyle_action(report_url, button_text):

    report_review_in_fyle_action = {
        'type': 'button',
        'text': {
            'type': 'plain_text',
            'text': button_text,
            'emoji': True
        },
        'action_id': 'review_report_in_fyle',
        'url': report_url
    }

    return report_review_in_fyle_action


def get_report_approval_notification_message(report, employee_display_name, report_url):
    report_url = '{}/{}?org_id={}'.format(report_url, report['id'], report['org_id'])

    report_approval_message = get_report_section_blocks(report, employee_display_name)

    actions_block = {
        'type': 'actions',
        'elements': [
            {
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
        ]
    }

    report_review_action_element = get_report_review_in_fyle_action(report_url, 'Review in Fyle')

    actions_block['elements'].append(report_review_action_element)

    report_approval_message.append(actions_block)

    return report_approval_message
