import datetime
from typing import Dict, List


# is_additional_field is for fields which are not custom fields but are part of a specific categories
def generate_field_ui(field_details: Dict, is_additional_field: bool = False) -> Dict:
    block_id = '{}_block'.format(field_details['column_name'])
    action_id = field_details['column_name']

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


def get_amount_and_currency_block(additional_currency_details: Dict = None) -> List:
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
            'action_id': 'currency',
        },
        'label': {'type': 'plain_text', 'text': 'Currency', 'emoji': True},
    }

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

    blocks.append(amount_block)

    if additional_currency_details is not None:
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


def get_default_fields_blocks(fields_render_property: Dict, additional_currency_details: Dict = None) -> List:

    default_fields_blocks = get_amount_and_currency_block(additional_currency_details)

    if fields_render_property['transaction_date'] is True:
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
        default_fields_blocks.append(date_of_spend_block)

    if fields_render_property['purpose'] is True:
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
        default_fields_blocks.append(purpose_block)

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
            'initial_option': {
                'text': {
                    'type': 'plain_text',
                    'text': 'Paid by me',
                    'emoji': True,
                },
                'value': 'true',
            },
            'options': [
                {
                    'text': {
                        'type': 'plain_text',
                        'text': 'Paid by me',
                        'emoji': True,
                    },
                    'value': 'true',
                },
                {
                    'text': {
                        'type': 'plain_text',
                        'text': 'Paid by company',
                        'emoji': True,
                    },
                    'value': 'false',
                },
            ],
            'action_id': 'is_reimbursable',
        },
        'label': {'type': 'plain_text', 'text': 'Payment Mode', 'emoji': True},
    }
    default_fields_blocks.append(payment_mode_block)

    if fields_render_property['vendor'] is True:
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
        default_fields_blocks.append(merchant_block)

    return default_fields_blocks


def get_projects_and_billable_block(selected_project: Dict = None) -> Dict:
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
    if selected_project is not None:
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
        'type': 'actions',
        'block_id': 'billable_block',
        'elements': [
            {
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
            }
        ]
    }

    return project_block, billable_block


def get_categories_block() -> Dict:
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

    return category_block


def get_cost_centers_block() -> Dict:
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
    return cost_centers_block


def expense_dialog_form(fields_render_property: Dict = None, selected_project: Dict = None, custom_fields: Dict = None, current_ui_blocks: List = None, additional_currency_details: Dict = None) -> Dict:
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
        ui_blocks = []

        ignore_block_id_list = ['custom_field', 'project_block', 'billable_block', 'category_block', 'cost_center_block', 'additional_field']
        additional_currency_amount_blocks = ['NUMBER_default_field_total_amount_block', 'TEXT_default_field_currency_context_block']

        is_additional_currency_amount_blocks_present = False
        for block in current_ui_blocks:
            if any(substring == block['block_id'] for substring in additional_currency_amount_blocks) is True:
                is_additional_currency_amount_blocks_present = True

        if is_additional_currency_amount_blocks_present is True:
            # Removing all exchange rate context blocks
            current_ui_blocks = current_ui_blocks[4:]
        else:
            # Removing currency and amount blocks only
            current_ui_blocks = current_ui_blocks[2:]

        # When additional currency details are present, render exchange rate context and total amount block
        if additional_currency_details is not None or is_additional_currency_amount_blocks_present is True:

            currency_block, amount_block, currency_context_block, total_amount_block = get_amount_and_currency_block(additional_currency_details)
            current_ui_blocks.insert(0, currency_block)
            current_ui_blocks.insert(1, currency_context_block)

            current_ui_blocks.insert(2, amount_block)
            current_ui_blocks.insert(3, total_amount_block)

        # When additional currency details are not present, render amount and currency blocks only
        else:

            currency_block, amount_block, currency_context_block, total_amount_block = get_amount_and_currency_block()
            current_ui_blocks.insert(0, currency_block)
            current_ui_blocks.insert(1, amount_block)

        cost_center_block = None
        for block in current_ui_blocks:
            # Removing cost center if present to maintain order of cost center at end of form
            if block is not None and block['block_id'] == 'cost_center_block':
                cost_center_block = block

            # Removing these block as these should not be rendered from current/cached UI block
            if block is not None and any(substring in block['block_id'] for substring in ignore_block_id_list) is False:
                ui_blocks.append(block)

        view['blocks'] = ui_blocks

    else:

        view['blocks'] = get_default_fields_blocks(fields_render_property)

    if fields_render_property['project'] is True:

        project_block, billable_block = get_projects_and_billable_block(selected_project)

        view['blocks'].append(project_block)

        view['blocks'].append(billable_block)

    # Since category block is dependent of projects sometimes, render them everytime.
    category_block = get_categories_block()

    view['blocks'].append(category_block)


    # If custom fields are present, render them in the form
    if custom_fields is not None and custom_fields['count'] > 0:
        for field in custom_fields['data']:

            # Additional fields are field which are not custom fields but are dependent on categories
            is_additional_field = False
            if field['is_custom'] is False:
                is_additional_field = True

            custom_field = generate_field_ui(field, is_additional_field=is_additional_field)
            view['blocks'].append(custom_field)

    # Render cost center from current ui blocks if present
    # This check is needed again here to maintain order
    if current_ui_blocks is not None and cost_center_block is not None:
        view['blocks'].append(cost_center_block)
    else:
        if fields_render_property['cost_center'] is True:

            cost_center_block = get_cost_centers_block()

            view['blocks'].append(cost_center_block)

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


def expense_dialog_form_v2(fields_render_property: Dict = None, selected_project: Dict = None, custom_fields: Dict = None, additional_currency_details: Dict = None) -> Dict:
    view = {
        'type': 'modal',
        'callback_id': 'create_expense',
        'title': {'type': 'plain_text', 'text': 'Create Expense', 'emoji': True},
        'submit': {'type': 'plain_text', 'text': 'Add Expense', 'emoji': True},
        'close': {'type': 'plain_text', 'text': 'Cancel', 'emoji': True}
    }

    view['blocks'] = []

    view['blocks'] = get_default_fields_blocks(fields_render_property, additional_currency_details)

    if fields_render_property['project'] is True:

        project_block, billable_block = get_projects_and_billable_block(selected_project)

        view['blocks'].append(project_block)

        view['blocks'].append(billable_block)

    category_block = get_categories_block()

    view['blocks'].append(category_block)


    # If custom fields are present, render them in the form
    if custom_fields is not None and custom_fields['count'] > 0:
        for field in custom_fields['data']:

            # Additional fields are field which are not custom fields but are dependent on categories
            is_additional_field = False
            if field['is_custom'] is False:
                is_additional_field = True

            custom_field = generate_field_ui(field, is_additional_field=is_additional_field)
            view['blocks'].append(custom_field)

    if fields_render_property['cost_center'] is True:

        cost_center_block = get_cost_centers_block()

        view['blocks'].append(cost_center_block)

    return view
