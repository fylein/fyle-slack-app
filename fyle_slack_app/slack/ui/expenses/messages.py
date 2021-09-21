import datetime
from typing import Dict, List


# is_additional_field is for fields which are not custom fields but are part of a specific categories
def generate_fields_ui(field_details: Dict, is_additional_field: bool = False) -> Dict:
    block_id = '{}_block'.format(field_details['column_name'])
    action_id = field_details['column_name']

    # We need to define addtional fields as custom fields so that we can clear them out in form when category is changed
    if field_details['is_custom'] is True or is_additional_field is True:
        block_id = '{}_custom_field_{}_block'.format(field_details['type'], field_details['column_name'])
        if field_details['is_custom'] is True:
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


def generate_expense_fields_mandatory_mapping(expense_fields: Dict) -> Dict:
    mandatory_mapping = {
        'purpose': False,
        'txn_dt': False,
        'vendor_id': False,
        'project_id': False,
        'cost_center_id': False
    }

    for field in expense_fields['data']:
        if field['column_name'] in mandatory_mapping:
            mandatory_mapping[field['column_name']] = field['is_mandatory']

    return mandatory_mapping


def get_default_fields_blocks(mandatory_mapping: Dict) -> List:
    default_fields_blocks = [
        {
            'type': 'input',
            'block_id': 'default_field_currency_block',
            'element': {
                'type': 'external_select',
                'placeholder': {
                    'type': 'plain_text',
                    'text': 'Select Currency',
                    'emoji': True,
                },
                'min_query_length': 0,
                'action_id': 'currency',
            },
            'label': {'type': 'plain_text', 'text': 'Currency', 'emoji': True},
        },
        {
            'type': 'input',
            'block_id': 'default_field_amount_block',
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
            'block_id': 'default_field_payment_mode_block',
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
    ]
    if mandatory_mapping['purpose'] is True:
        purpose_block = {
            'type': 'input',
            'block_id': 'default_field_purpose_block',
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
        default_fields_blocks.append(purpose_block)

    if mandatory_mapping['txn_dt'] is True:
        date_of_spend_block = {
            'type': 'input',
            'block_id': 'default_field_date_of_spend_block',
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
        default_fields_blocks.append(date_of_spend_block)

    if mandatory_mapping['vendor_id'] is True:
        merchant_block = {
            'type': 'input',
            'block_id': 'default_field_merchant_block',
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
        default_fields_blocks.append(merchant_block)

    return default_fields_blocks


def expense_dialog_form(expense_fields: Dict = None, projects: Dict = None, custom_fields: Dict = None, categories: Dict = None, current_ui_blocks: List = None) -> Dict:
    view = {
        'type': 'modal',
        'callback_id': 'create_expense',
        'title': {'type': 'plain_text', 'text': 'Create Expense', 'emoji': True},
        'submit': {'type': 'plain_text', 'text': 'Add Expense', 'emoji': True},
        'close': {'type': 'plain_text', 'text': 'Cancel', 'emoji': True}
    }

    view['blocks'] = []

    # If current UI blocks are passed use them as it is for faster processing of UI elements.
    if current_ui_blocks is not None:
        view['blocks'] = current_ui_blocks
    else:
        mandatory_mapping = generate_expense_fields_mandatory_mapping(expense_fields)

        view['blocks'] = get_default_fields_blocks(mandatory_mapping)

        if mandatory_mapping['project_id'] is True and projects is not None and projects['count'] > 0:
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

    # Since category block is dependent of projects sometimes, render them everytime.
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

    if categories is not None and categories['count'] > 0:
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
        category_block['element']['initial_option'] = category_options[0]
    else:
        category_block['element']['min_query_length'] = 0

    view['blocks'].append(category_block)


    # If custom fields are present, render them in the form
    if custom_fields is not None and custom_fields['count'] > 0:
        for field in custom_fields['data']:

            # Additional fields are field which are not custom fields but are dependent on categories
            is_additional_field = False
            if field['is_custom'] is False:
                is_additional_field = True

            custom_field = generate_fields_ui(field, is_additional_field=is_additional_field)
            view['blocks'].append(custom_field)

    return view


def expense_form_loading_modal() -> Dict:
    loading_modal = {
        'type': 'modal',
        'callback_id': 'create_expense',
        'title': {'type': 'plain_text', 'text': 'Create Expense', 'emoji': True},
        'close': {'type': 'plain_text', 'text': 'Cancel', 'emoji': True},
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': 'Loading the best expense form :zap:'
                }
            }
        ]
    }

    return loading_modal
