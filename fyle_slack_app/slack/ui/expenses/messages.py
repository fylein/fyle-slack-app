import datetime
from typing import Dict


def generate_fields_ui(field_details: Dict) -> Dict:
    block_id = '{}_block'.format(field_details['column_name'])
    action_id = field_details['column_name']

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


def expense_dialog_form(expense_fields, projects, custom_fields=None, categories=None):
    view = {
        'type': 'modal',
        'callback_id': 'create_expense',
        'title': {'type': 'plain_text', 'text': 'Create Expense', 'emoji': True},
        'submit': {'type': 'plain_text', 'text': 'Add Expense', 'emoji': True},
        'close': {'type': 'plain_text', 'text': 'Cancel', 'emoji': True},
        'blocks': [
            {
                'type': 'input',
                'block_id': 'currency_block',
                'element': {
                    'type': 'static_select',
                    'placeholder': {
                        'type': 'plain_text',
                        'text': 'Select Currency',
                        'emoji': True,
                    },
                    'options': [
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': 'INR',
                                'emoji': True,
                            },
                            'value': 'INR',
                        },
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': 'USD',
                                'emoji': True,
                            },
                            'value': 'USD',
                        },
                    ],
                    'action_id': 'currency',
                },
                'label': {'type': 'plain_text', 'text': 'Currency', 'emoji': True},
            },
            {
                'type': 'input',
                'block_id': 'amount_block',
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
            },
            {
                'type': 'input',
                'block_id': 'payment_mode_block',
                'element': {
                    'type': 'static_select',
                    'placeholder': {
                        'type': 'plain_text',
                        'text': 'Select Payment Mode',
                        'emoji': True,
                    },
                    'initial_option': {
                        'text': {
                            'type': 'plain_text',
                            'text': 'Paid by me',
                            'emoji': True,
                        },
                        'value': 'paid_by_me',
                    },
                    'options': [
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': 'Paid by me',
                                'emoji': True,
                            },
                            'value': 'paid_by_me',
                        },
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': 'Paid by company',
                                'emoji': True,
                            },
                            'value': 'paid_by_company',
                        },
                    ],
                    'action_id': 'payment_mode',
                },
                'label': {'type': 'plain_text', 'text': 'Payment Mode', 'emoji': True},
            },
        ],
    }

    purpose_block = {
        'type': 'input',
        'block_id': 'purpose_block',
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
    view['blocks'].append(purpose_block)

    date_of_spend_block = {
        'type': 'input',
        'block_id': 'date_of_spend_block',
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
    view['blocks'].append(date_of_spend_block)

    merchant_block = {
        'type': 'input',
        'block_id': 'merchant_block',
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
    view['blocks'].append(merchant_block)

    if projects['count'] > 0:
        project_block = {
            'type': 'input',
            'block_id': 'project_block',
            'dispatch_action': True,
            'element': {
                'type': 'static_select',
                'action_id': 'project',
            },
            'label': {'type': 'plain_text', 'text': 'Project', 'emoji': True},
        }
        project_options = []
        for project in projects['data']:
            project_options.append({
                'text': {
                    'type': 'plain_text',
                    'text': project['display_name'],
                    'emoji': True,
                },
                'value': str(project['id']),
            })
        project_block['element']['options'] = project_options

        view['blocks'].append(project_block)

    category_block = {
        'type': 'input',
        'block_id': 'category_block',
        'dispatch_action': True,
        'element': {
            'type': 'external_select',
            'placeholder': {
                'type': 'plain_text',
                'text': 'Eg. Travel',
                'emoji': True,
            },
            'action_id': 'category',
        },
        'label': {'type': 'plain_text', 'text': 'Category', 'emoji': True},
    }

    if categories is not None:
        category_block['element']['type'] = 'static_select'
        category_options = []

        for category in categories['data']:
            category_options.append({
                'text': {
                    'type': 'plain_text',
                    'text': category['display_name'],
                    'emoji': True,
                },
                'value': str(category['id']),
            })
        category_block['element']['options'] = category_options
    else:
        category_block['element']['min_query_length'] = 0

    view['blocks'].append(category_block)



    if custom_fields is not None:
        for field in custom_fields:
            custom_field = generate_fields_ui(field)
            view['blocks'].append(custom_field)

    # if form_state is not None:
    # 	for block in view['blocks']:
    # 		print('BLOCK ID -> ', block['block_id'])
    # 		value_key = 'value'
    # 		initial_value_key = 'initial_value'
    # 		if block['element']['type'] == 'static_select':
    # 			value_key = 'selected_option'
    # 			initial_value_key = 'initial_option'
    # 		elif block['element']['type'] == 'datepicker':
    # 			value_key = 'selected_date'
    # 			initial_value_key = 'initial_date'

    # 		block['element'][initial_value_key] = form_state[block['block_id']][block['element']['action_id']][value_key]

    return view
