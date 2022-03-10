from typing import Dict

from fyle_slack_app.models import User
from fyle_slack_app.libs import utils

from fyle_slack_app.fyle import utils as fyle_utils


def get_report_expenses_dialog(user: User, report: dict, private_metadata: str, report_expenses: dict) -> Dict:

    '''
    NOTE: Before increasing the block elements of this modal, please make sure that the total count does not exceed 100, 
    since slack has set a limit of 100.
    '''

    report_expenses_dialog = {
        'type': 'modal',
        'callback_id': 'report_approval_from_modal',
        'private_metadata': private_metadata,
        'title': {
            'type': 'plain_text',
            'text': 'Report Details',

        },
        'submit': {
            'type': 'plain_text',
            'text': ':rocket: Approve'
        },
        'type': 'modal',
        'close': {
            'type': 'plain_text',
            'text': 'Close',
            'emoji': True
        },
        'blocks': [
            {
                'type': 'divider'
            },
            {
                'type': 'section',
                'fields': [
                    {
                        'type': 'mrkdwn',
                        'text': 'Report Name:\n *<{}|{}>*'.format(report['url'], report['name'])
                    },
                    {
                        'type': 'mrkdwn',
                        'text': 'Spender:\n *{}*'.format(report['spender_email'])
                    }
                ]
            },
            {
                'type': 'context',
                'elements': [
                    {
                        'type': 'image',
                        'image_url': 'https://api.slack.com/img/blocks/bkb_template_images/placeholder.png',
                        'alt_text': 'placeholder'
                    }
                ]
            }
        ]
    }

    if report_expenses is not None:

        # Add expenses-list block title
        expenses_section_title = {
            'type': 'context',
            'elements': [
                {
                    'type': 'mrkdwn',
                    'text': ':page_facing_up: *Expenses ({}) for {} {}*'.format(report['num_expenses'], report['currency'], report['amount'])
                }
            ]
        }
        report_expenses_dialog['blocks'].append(expenses_section_title)

        expenses_count = 0

        # Iterate and add all report expenses to append report_expenses_dialog message
        for expense in report_expenses:

            # Restrict modal to show at-most 15 expenses
            if expenses_count > 15:
                break

            expense_block = [
                {
                    'type': 'divider'
                }
            ]
            
            # Compose and append the expense title message
            if expense['category'] and expense['category']['name'] and expense['category']['name'] != 'Unspecified':
                if expense['merchant']:
                    expense_initial_text = '*{} ({})*'.format(expense['category']['name'], expense['merchant'])
                else:
                    expense_initial_text = '*{}*'.format(expense['category']['name'])
            else:
                expense_initial_text = 'An'
            
            expense_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, expense, 'EXPENSE')
            expense_block_title = {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '{} expense of :dollar: *<{}|{} {}>*'.format(expense_initial_text, expense_url, expense['currency'], expense['amount'])
                }
            }
            expense_block.append(expense_block_title)

            # Compose and append expense block fields
            readable_spend_date = utils.get_formatted_datetime(expense['spent_at'], '%B %d, %Y')
            expense_block_fields = {
                'type': 'section',
                'fields': [
                    {
                        'type': 'mrkdwn',
                        'text': 'Date of Spend:\n *{}*'.format(readable_spend_date)
                    }
                ]
            }

            is_receipt_attached_message = ':white_check_mark: *Attached*' if len(expense['file_ids']) > 0 else ':x: *Missing*'
            expense_block_fields['fields'].append({
                'type': 'mrkdwn',
                'text': 'Receipt:\n {}'.format(is_receipt_attached_message)
            })

            expense_block.append(expense_block_fields)

            # Show expense-purpose field only if is present
            if expense['purpose']:
                expense_block.append({
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': 'Purpose:\n *{}*'.format(expense['purpose'])
                        }
                    ]
                })
            
            # Add a bit of space after each expense
            expense_block.append({
                'type': 'section',
                'fields': [
                    {
                        'type': 'mrkdwn',
                        'text': ' '
                    }
                ]
            })

            # Add expense block to the modal message
            report_expenses_dialog['blocks'] += expense_block
            expenses_count += 1

        # Show a hyperlink to redirect the user to fyle web-app, if a report has more than 15 expenses
        if report['num_expenses'] > 15:
            view_more_expenses_message = [
                {
                    'type': 'divider'
                },
                {
                    'type': 'context',
                    'elements': [
                        {
                            'type': 'mrkdwn',
                            'text': '<{}|*View rest of the expenses in Fyle*> :arrow_upper_right:'.format(report['url'])
                        }
                    ]
                }
            ]
            report_expenses_dialog['blocks'] += view_more_expenses_message
        
    else:
        loading_message = [
            {
                'type': 'context',
                'elements': [
                    {
                        'type': 'mrkdwn',
                        'text': '*Loading report\'s expenses....* :hourglass_flowing_sand:'
                    }
                ]
            }
        ]
        report_expenses_dialog['blocks'] += loading_message

    return report_expenses_dialog
