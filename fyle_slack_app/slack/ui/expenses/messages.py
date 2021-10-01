from typing import Any, Dict, List

import datetime

from fyle_slack_app.libs import utils


def get_custom_field_value(custom_fields: List, action_id) -> Any:
    pass


# is_additional_field is for fields which are not custom fields but are part of a specific categories
def generate_field_ui(field_details: Dict, is_additional_field: bool = False) -> Dict:
    block_id = '{}_block'.format(field_details['column_name'])
    action_id = field_details['column_name']

    custom_field = None

    # We need to define addtional fields as custom fields so that we can clear them out in form when category is changed
    if field_details['is_custom'] is True or is_additional_field is True:
        block_id = '{}_additional_field_{}_block'.format(field_details['type'], field_details['column_name'])
        if field_details['is_custom'] is True:
            block_id = '{}_custom_field_{}_block'.format(field_details['type'], field_details['column_name'])
            action_id = '{}'.format(field_details['field_name'])

    if field_details['type'] in ['NUMBER', 'TEXT']:
        custom_field = {
            'type': 'input',
            'block_id': block_id,
            'label': {
                'type': 'plain_text',
                'text': '{}'.format(field_details['field_name']),
            },
            'element': {
                'type': 'plain_text_input',
                'action_id': action_id,
                'placeholder': {
                    'type': 'plain_text',
                    'text': '{}'.format(field_details['placeholder']),
                },
            },
        }

    elif field_details['type'] in ['SELECT', 'MULTI_SELECT']:

        if field_details['type'] == 'SELECT':
            field_type = 'static_select'
        elif field_details['type'] == 'MULTI_SELECT':
            field_type = 'multi_static_select'

        custom_field = {
            'type': 'input',
            'label': {
                'type': 'plain_text',
                'text': '{}'.format(field_details['field_name']),
                'emoji': True,
            },
            'block_id': block_id,
            'element': {
                'type': field_type,
                'placeholder': {
                    'type': 'plain_text',
                    'text': '{}'.format(field_details['placeholder']),
                    'emoji': True,
                },
                'action_id': action_id,
            },
        }

        custom_field['element']['options'] = []

        for option in field_details['options']:
            custom_field['element']['options'].append(
                {
                    'text': {
                        'type': 'plain_text',
                        'text': option,
                        'emoji': True,
                    },
                    'value': option,
                }
            )

    elif field_details['type'] == 'BOOLEAN':
        custom_field = {
            'type': 'input',
            'block_id': block_id,
            'optional': True,
            'element': {
                'type': 'checkboxes',
                'options': [
                    {
                        'text': {
                            'type': 'plain_text',
                            'text': '{}'.format(field_details['field_name']),
                            'emoji': True,
                        }
                    }
                ],
                'action_id': action_id,
            },
            'label': {
                'type': 'plain_text',
                'text': '{}'.format(field_details['field_name']),
                'emoji': True,
            },
        }

    elif field_details['type'] == 'DATE':
        custom_field = {
            'type': 'input',
            'block_id': block_id,
            'element': {
                'type': 'datepicker',
                'placeholder': {
                    'type': 'plain_text',
                    'text': '{}'.format(field_details['placeholder']),
                    'emoji': True,
                },
                'action_id': 'spent_at',
            },
            'label': {
                'type': 'plain_text',
                'text': '{}'.format(field_details['field_name']),
                'emoji': True
            },
        }

    return custom_field


def get_amount_and_currency_block(additional_currency_details: Dict = None, expense: Dict = None) -> List:
    blocks = []

    currency_block = {
        'type': 'input',
        'block_id': 'SELECT_default_field_currency_block',
        'dispatch_action': True,
        'element': {
            'type': 'external_select',
            'placeholder': {
                'type': 'plain_text',
                'text': 'Select Currency',
                'emoji': True,
            },
            'min_query_length': 1,
            'initial_option': {
                'text': {
                    'type': 'plain_text',
                    'text': additional_currency_details['home_currency'],
                    'emoji': True,
                },
                'value': additional_currency_details['home_currency'],
            },
            'action_id': 'currency',
        },
        'label': {'type': 'plain_text', 'text': 'Currency', 'emoji': True},
    }

    if expense is not None:
        currency_block['element']['initial_option']['text']['text'] = expense['currency']
        currency_block['element']['initial_option']['value'] = expense['currency']

    blocks.append(currency_block)

    currency_context_block = None
    total_amount_block = None
    amount_block = {
        'type': 'input',
        'block_id': 'NUMBER_default_field_amount_block',
        'element': {
            'type': 'plain_text_input',
            'placeholder': {
                'type': 'plain_text',
                'text': 'Enter Amount',
                'emoji': True,
            },
            'action_id': 'amount',
        },
        'label': {'type': 'plain_text', 'text': 'Amount', 'emoji': True},
    }

    if expense is not None:
        amount_block['element']['initial_value'] = str(expense['amount'])

    blocks.append(amount_block)

    if expense is not None and expense['foreign_currency'] is not None:
        additional_currency_details = {
            'home_currency': expense['currency'],
            'foreign_currency': expense['foreign_currency'],
            'total_amount': str(expense['foreign_amount'])
        }

    if 'foreign_currency' in additional_currency_details:
        amount_block['dispatch_action'] = True
        amount_block['element']['dispatch_action_config'] = {
            'trigger_actions_on': [
                'on_character_entered'
            ]
        }

        amount_block['element']['placeholder']['text'] = 'Enter Amount {}'.format(additional_currency_details['foreign_currency'])

        currency_context_block = {
			'type': 'context',
            'block_id': 'TEXT_default_field_currency_context_block',
			'elements': [
				{
					'type': 'mrkdwn',
					'text': ':information_source: Amount ({}) x Exchange Rate = Total ({})'.format(additional_currency_details['foreign_currency'], additional_currency_details['home_currency'])
				}
			]
		}

        blocks.insert(1, currency_context_block)

        total_amount_block = {
            'type': 'input',
            'block_id': 'NUMBER_default_field_total_amount_block',
            'element': {
                'type': 'plain_text_input',
                'placeholder': {
                    'type': 'plain_text',
                    'text': 'Enter Total Amount {}'.format(additional_currency_details['home_currency']),
                    'emoji': True,
                },
                'action_id': 'foreign_amount',
            },
            'label': {'type': 'plain_text', 'text': 'Total Amount', 'emoji': True},
        }

        if int(additional_currency_details['total_amount']) != 0:
            total_amount_block['element']['initial_value'] = str(additional_currency_details['total_amount'])

        blocks.insert(3, total_amount_block)

    return blocks


def get_default_fields_blocks(additional_currency_details: Dict = None, expense: Dict = None) -> List:

    default_fields_blocks = get_amount_and_currency_block(additional_currency_details, expense)

    date_of_spend_block = {
        'type': 'input',
        'block_id': 'DATE_default_field_date_of_spend_block',
        'element': {
            'type': 'datepicker',
            'initial_date': datetime.datetime.today().strftime('%Y-%m-%d'),
            'placeholder': {
                'type': 'plain_text',
                'text': 'Select a date',
                'emoji': True,
            },
            'action_id': 'spent_at',
        },
        'label': {'type': 'plain_text', 'text': 'Date of Spend', 'emoji': True},
    }

    if expense is not None:
        date_of_spend_block['element']['initial_date'] = utils.get_formatted_datetime(expense['spent_at'], '%Y-%m-%d')

    default_fields_blocks.append(date_of_spend_block)

    purpose_block = {
        'type': 'input',
        'block_id': 'TEXT_default_field_purpose_block',
        'element': {
            'type': 'plain_text_input',
            'placeholder': {
                'type': 'plain_text',
                'text': 'Eg. Client Meeting',
                'emoji': True,
            },
            'action_id': 'purpose',
        },
        'label': {'type': 'plain_text', 'text': 'Purpose', 'emoji': True},
    }

    if expense is not None:
        purpose_block['element']['initial_value'] = expense['purpose']

    default_fields_blocks.append(purpose_block)

    paid_by_me_option = {
        'text': {
            'type': 'plain_text',
            'text': 'Paid by me',
            'emoji': True,
        },
        'value': 'true',
    }

    paid_by_company_option = {
        'text': {
            'type': 'plain_text',
            'text': 'Paid by company',
            'emoji': True,
        },
        'value': 'false',
    }

    payment_mode_block = {
        'type': 'input',
        'block_id': 'SELECT_default_field_payment_mode_block',
        'element': {
            'type': 'static_select',
            'placeholder': {
                'type': 'plain_text',
                'text': 'Select Payment Mode',
                'emoji': True,
            },
            'initial_option': paid_by_me_option,
            'options': [paid_by_me_option, paid_by_company_option],
            'action_id': 'is_reimbursable',
        },
        'label': {'type': 'plain_text', 'text': 'Payment Mode', 'emoji': True},
    }

    if expense is not None:
        if expense['is_reimbursable'] is False:
            payment_mode_block['element']['initial_option'] = paid_by_company_option

    default_fields_blocks.append(payment_mode_block)

    merchant_block = {
        'type': 'input',
        'block_id': 'TEXT_default_field_merchant_block',
        'element': {
            'type': 'plain_text_input',
            'placeholder': {
                'type': 'plain_text',
                'text': 'Eg. Uber',
                'emoji': True,
            },
            'action_id': 'merchant',
        },
        'label': {'type': 'plain_text', 'text': 'Merchant', 'emoji': True},
    }

    if expense is not None:
        merchant_block['element']['initial_value'] = expense['merchant']

    default_fields_blocks.append(merchant_block)

    return default_fields_blocks


def get_projects_and_billable_block(selected_project: Dict = None, expense: Dict = None) -> Dict:
    project_block = {
        'type': 'input',
        'block_id': 'project_block',
        'dispatch_action': True,
        'element': {
            'min_query_length': 0,
            'type': 'external_select',
            'placeholder': {
                'type': 'plain_text',
                'text': 'Eg. Travel',
                'emoji': True,
            },

            'action_id': 'project_id',
        },
        'label': {'type': 'plain_text', 'text': 'Project', 'emoji': True},
    }

    if expense is not None:
        project_block['element']['initial_option'] = {
            'text': {
                'type': 'plain_text',
                'text': expense['project']['name'],
                'emoji': True,
            },
            'value': str(expense['project']['id']),
        }
    elif selected_project is not None:
        selected_project = selected_project['data'][0]

        project_display_name = selected_project['display_name']
        if selected_project['name'] == selected_project['sub_project']:
            project_display_name = selected_project['name']
        project_block['element']['initial_option'] = {
            'text': {
                'type': 'plain_text',
                'text': project_display_name,
                'emoji': True,
            },
            'value': str(selected_project['id']),
        }

    billable_block = {
        'type': 'input',
        'block_id': 'billable_block',
        'element': {
            'type': 'checkboxes',
            'options': [
                {
                    'text': {
                        'type': 'plain_text',
                        'text': 'Billable',
                        'emoji': True
                    }
                }
            ],
            'action_id': 'is_billable'
        },
        'label': {'type': 'plain_text', 'text': 'Billable', 'emoji': True},
    }

    return project_block, billable_block


def get_categories_block(expense: Dict = None) -> Dict:
    category_block = {
        'type': 'input',
        'block_id': 'category_block',
        'dispatch_action': True,
        'element': {
            'type': 'external_select',
            'min_query_length': 0,
            'placeholder': {
                'type': 'plain_text',
                'text': 'Eg. Food',
                'emoji': True,
            },
            'action_id': 'category_id',
        },
        'label': {'type': 'plain_text', 'text': 'Category', 'emoji': True},
    }

    if expense is not None:
        category_block['element']['initial_option'] = {
            'text': {
                'type': 'plain_text',
                'text': expense['category']['name'],
                'emoji': True,
            },
            'value': str(expense['category']['id']),
        }

    return category_block


def get_cost_centers_block(expense: Dict = None) -> Dict:
    cost_centers_block = {
        'type': 'input',
        'block_id': 'cost_center_block',
        'element': {
            'type': 'external_select',
            'min_query_length': 0,
            'placeholder': {
                'type': 'plain_text',
                'text': 'Eg. Accounting',
                'emoji': True,
            },
            'action_id': 'cost_center_id',
        },
        'label': {'type': 'plain_text', 'text': 'Cost Center', 'emoji': True},
    }

    if expense is not None:
        cost_centers_block['element']['initial_option'] = {
            'text': {
                'type': 'plain_text',
                'text': expense['cost_center']['name'],
                'emoji': True,
            },
            'value': str(expense['cost_center']['id']),
        }
    return cost_centers_block


def expense_form_loading_modal(title: str, loading_message: str) -> Dict:
    loading_modal = {
        'type': 'modal',
        'callback_id': 'upsert_expense',
        'title': {'type': 'plain_text', 'text': '{}'.format(title), 'emoji': True},
        'close': {'type': 'plain_text', 'text': 'Cancel', 'emoji': True},
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '{}'.format(loading_message)
                }
            }
        ]
    }

    return loading_modal


def get_add_to_report_blocks(add_to_report: str) -> Dict:
    blocks = []
    add_to_existing_report_option = {
        'text': {
            'type': 'plain_text',
            'text': 'Add to Existing Report',
            'emoji': True
        },
        'value': 'existing_report'
    }

    add_to_new_report_option = {
        'text': {
            'type': 'plain_text',
            'text': 'Add to New Report',
            'emoji': True
        },
        'value': 'new_report'
    }
    add_to_report_block = {
        'type': 'input',
        'block_id': 'add_to_report_block',
        'dispatch_action': True,
        'element': {
            'type': 'radio_buttons',
            'options': [add_to_existing_report_option, add_to_new_report_option],
            'action_id': 'add_to_report'
        },
        'label': {
            'type': 'plain_text',
            'text': 'Add to Report',
            'emoji': True
        }
    }
    blocks.append(add_to_report_block)

    add_to_report_mapping = {
        'new_report': {
            'ui': {
                'type': 'input',
                'block_id': 'add_to_new_report_block',
                'element': {
                    'type': 'plain_text_input',
                    'placeholder': {
                        'type': 'plain_text',
                        'text': 'Enter Report Name',
                        'emoji': True
                    },
                    'action_id': 'report_name'
                },
                'label': {
                    'type': 'plain_text',
                    'text': 'Report Name',
                    'emoji': True
                }
            },
            'option': add_to_new_report_option
        },
        'existing_report': {
            'ui': {
                'type': 'input',
                'block_id': 'add_to_existing_report_block',
                'element': {
                    'type': 'external_select',
                    'placeholder': {
                        'type': 'plain_text',
                        'text': 'Select a Report',
                        'emoji': True
                    },
                    'action_id': 'existing_report'
                },
                'label': {
                    'type': 'plain_text',
                    'text': 'Select Report',
                    'emoji': True
                }
            },
            'option': add_to_existing_report_option
        }
    }

    if add_to_report is not None:
        add_to_report_details = add_to_report_mapping[add_to_report]
        add_to_report_additional_block = add_to_report_details['ui']
        selected_report_option = add_to_report_details['option']
        add_to_report_block['element']['initial_option'] = selected_report_option
        blocks.append(add_to_report_additional_block)

    return blocks


def expense_dialog_form(
        fields_render_property: Dict,
        selected_project: Dict = None,
        custom_fields: Dict = None,
        additional_currency_details: Dict = None,
        add_to_report: str = None,
        private_metadata: str = None,
        expense : Dict = None
    ) -> Dict:

    view = {
        'type': 'modal',
        'callback_id': 'upsert_expense',
        'private_metadata': private_metadata,
        'title': {'type': 'plain_text', 'text': 'Create Expense', 'emoji': True},
        'submit': {'type': 'plain_text', 'text': 'Add Expense', 'emoji': True},
        'close': {'type': 'plain_text', 'text': 'Cancel', 'emoji': True}
    }

    view['blocks'] = []

    view['blocks'] = get_default_fields_blocks(additional_currency_details, expense)

    if fields_render_property['project'] is True:

        project_block, billable_block = get_projects_and_billable_block(selected_project, expense)

        view['blocks'].append(project_block)

        view['blocks'].append(billable_block)

    category_block = get_categories_block(expense)

    view['blocks'].append(category_block)


    # If custom fields are present, render them in the form
    if custom_fields is not None:
        if isinstance(custom_fields, list):
            view['blocks'].extend(custom_fields)
        elif 'count' in custom_fields and custom_fields['count'] > 0:
            for field in custom_fields['data']:

                # Additional fields are field which are not custom fields but are dependent on categories
                is_additional_field = False
                if field['is_custom'] is False:
                    is_additional_field = True

                custom_field = generate_field_ui(field, is_additional_field=is_additional_field)
                if custom_field is not None:
                    view['blocks'].append(custom_field)

    if fields_render_property['cost_center'] is True:

        cost_center_block = get_cost_centers_block(expense)

        view['blocks'].append(cost_center_block)


    # Divider for add to report section
    view['blocks'].append({
        'type': 'divider'
    })

    if add_to_report is not None:
        add_to_report_blocks = get_add_to_report_blocks(add_to_report)

        view['blocks'].extend(add_to_report_blocks)

    return view


def view_expense_message(expense: Dict) -> Dict:
    from fyle_slack_app.slack.interactives import expense
    expense = expense['data']

    spent_at = utils.get_formatted_datetime(expense['spent_at'], '%B %d, %Y')

    receipt_message = ':x: Not Attached'
    if len(expense['file_ids']) > 0:
        receipt_message = ':white_check_mark: Attached'

    report_message = ':x: Not Added'
    if expense['report_id'] is not None:
        report_message = ':white_check_mark: Added'

    view_expense_blocks =  [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':money_with_wings: An expense of *{} {}* has been created!'.format(expense['currency'], expense['amount'])
            }
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Date of spend: * \n {}'.format(spent_at)
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Receipt: * \n {}'.format(receipt_message)
                }
            ]
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Report: * \n {}'.format(report_message)
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Expense Details: * \n Travel to Office (Uber)'
                }
            ]
        },
        {
        'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Edit Expense',
                        'emoji': True,
                    },
                    'value': expense['id'],
                    'action_id': 'edit_expense',
                }
            ],
        },
        {
            'type': 'context',
            'block_id': expense['id'],
            'elements': [
                {
                    'type': 'plain_text',
                    'text': 'Powered by Fyle',
                    'emoji': True,
                }
            ],
        }
    ]

    return view_expense_blocks
