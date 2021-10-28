from typing import Dict, List

from django.conf import settings

from fyle_slack_app.slack.ui.authorization import messages


def get_pre_authorization_message(user_name: str, fyle_oauth_url: str) -> Dict:
    pre_authorization_message_blocks = messages.get_pre_authorization_message(user_name, fyle_oauth_url)
    return {
        'type': 'home',
        'blocks': pre_authorization_message_blocks
    }


def get_unreported_expenses_section(expenses: Dict) -> List[Dict]:

    unreported_expenses_url = '{}/main/#/enterprise/my_expenses/?state=ready_to_report'.format(settings.FYLE_APP_URL)

    unreported_expenses_section = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '\n'
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':interrobang:  *Unreported Expenses ({})* \n Create a report and submit all your unreported expenses for approval'.format(expenses['count'])
            }
        },
        {
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'style': 'primary',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Report Expenses',
                        'emoji': True
                    },
                    'action_id': 'unreported_expenses'
                },
                {
                    'type': 'button',
                    'text': {
                        'type': 'plain_text',
                        'text': 'View in Fyle',
                        'emoji': True
                    },
                    'url': unreported_expenses_url,
                    'action_id': 'view_unreported_expenses_in_fyle'
                }
            ]
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '\n'
            }
        }
    ]

    return unreported_expenses_section



def get_incomplete_expenses_section(expenses: Dict) -> List[Dict]:

    incomplete_expenses_url = '{}/main/#/enterprise/my_expenses/?state=draft'.format(settings.FYLE_APP_URL)

    incomeplete_expenses_section = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '\n'
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':x:  *Incomplete Expenses ({})* \n View all your incomplete expenses in Fyle'.format(expenses['count'])
            }
        },
        {
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'text': {
                        'type': 'plain_text',
                        'text': 'View in Fyle',
                        'emoji': True
                    },
                    'url': incomplete_expenses_url,
                    'action_id': 'view_incomplete_expenses_in_fyle'
                }
            ]
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '\n'
            }
        }
    ]

    return incomeplete_expenses_section


def get_draft_reports_section(reports: Dict) -> List[Dict]:

    draft_reports_url = '{}/main/#/enterprise/my_reports/?state=draft'.format(settings.FYLE_APP_URL)

    draft_reports_section = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '\n'
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':open_file_folder: *Draft Reports ({})* \n View all your draft reports in Fyle'.format(reports['count'])
            }
        },
        {
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'text': {
                        'type': 'plain_text',
                        'text': 'View in Fyle',
                        'emoji': True
                    },
                    'url': draft_reports_url,
                    'action_id': 'view_draft_reports_in_fyle'
                }
            ]
        }
    ]

    return draft_reports_section


def get_base_dashboard_view(team_id: str) -> List[Dict]:

    messages_deeplink_url = 'slack://app?id={}&team={}&tab=messages'.format(settings.SLACK_APP_ID, team_id)

    dashboard_view = {
        'type': 'home',
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': ':wave: *Hey Shreyansh, I am :robot_face: Fyle Bot. Welcome to the Fyle dashboard!*'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': 'I can help you :money_with_wings: add expenses, :writing_hand: manage expenses, :receipt: upload receipts, :inbox_tray: submit reports and :zap: get instant notifications all here on Slack'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '\n'
                }
            },
            {
                'type': 'divider'
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '\n'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': ':money_with_wings: *Create expenses instantly by uploading a receipt!* \n Upload receipts to auto create an expense instantly or add an expense manually'
                }
            },
            {
                'type': 'actions',
                'elements': [
                    {
                        'type': 'button',
                        'style': 'primary',
                        'text': {
                            'type': 'plain_text',
                            'text': 'Upload Receipts',
                            'emoji': True
                        },
                        'url': messages_deeplink_url,
                        'action_id': 'create_expense_using_receipts'
                    },
                    {
                        'type': 'button',
                        'text': {
                            'type': 'plain_text',
                            'text': 'Create Manually',
                            'emoji': True
                        },
                        'action_id': 'create_expense_manually'
                    }
                ]
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '\n'
                }
            }
        ]
    }


    return dashboard_view



def get_post_authorization_message(team_id: str, unreported_expenses: Dict, incomplete_expenses: Dict, draft_reports: Dict) -> Dict:

    dashboard_view = get_base_dashboard_view(team_id)

    if unreported_expenses['count'] > 0:
        dashboard_view['blocks'].append(
            {
                'type': 'divider'
            }
        )
        unreported_expenses_section = get_unreported_expenses_section(unreported_expenses)

        dashboard_view['blocks'].extend(unreported_expenses_section)

    if incomplete_expenses['count'] > 0:
        dashboard_view['blocks'].append(
            {
                'type': 'divider'
            }
        )
        incomplete_expenses_section = get_incomplete_expenses_section(incomplete_expenses)

        dashboard_view['blocks'].extend(incomplete_expenses_section)

    if draft_reports['count'] > 0:
        dashboard_view['blocks'].append(
            {
                'type': 'divider'
            }
        )
        draft_reports_section = get_draft_reports_section(draft_reports)

        dashboard_view['blocks'].extend(draft_reports_section)

    return dashboard_view
