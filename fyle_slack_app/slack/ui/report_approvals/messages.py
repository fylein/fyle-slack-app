import datetime


def get_report_section_blocks(report, employee_display_name):

    submitted_at = datetime.datetime.fromisoformat(report['submitted_at'])
    readable_submitted_at = submitted_at.strftime('%B %d, %Y')

    return [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*{}* ( {} ) submitted an expense report [ {} ] for your approval'.format(employee_display_name, report['employee']['user']['email'], report['claim_number'])
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
                    'text': '*Amount:* {} {} \n *No. of expenses:* {}'.format(report['currency'], report['amount'], report['num_expenses'])
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Submitted On:* {}'.format(readable_submitted_at)
                }
            ]
        }
    ]


def get_report_approval_notification_message(report, approver_id, employee_display_name, cluster_domain):
    REPORT_WEBAPP_URL = '{}/app/main/#/enterprise/reports/{}?org_id={}'.format(cluster_domain, report['id'], report['org_id'])

    report_approval_message = get_report_section_blocks(report, employee_display_name)

    actions_block = {
        'type': 'actions',
        'elements': []
    }

    report_approve_action_element = {
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

    report_review_action_element = {
        'type': 'button',
        'text': {
            'type': 'plain_text',
            'text': 'Review in Fyle',
            'emoji': True
        },
        'action_id': 'report_review_in_fyle',
        'url': REPORT_WEBAPP_URL
    }

    for approval in report['approvals']:
        if approval['approver_id'] == approver_id:
            # Show `Approve` button only if report and approval states are below mentioned states
            if report['state'] == 'APPROVER_PENDING' and approval['state'] == 'APPROVAL_PENDING':
                actions_block['elements'].append(report_approve_action_element)

    actions_block['elements'].append(report_review_action_element)

    report_approval_message.append(actions_block)

    return report_approval_message