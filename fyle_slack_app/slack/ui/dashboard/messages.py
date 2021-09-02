import json
from random import random
from typing import Dict

import datetime

from fyle_slack_app.slack.ui.authorization import messages


def get_pre_authorization_message(user_name: str, fyle_oauth_url: str) -> Dict:
    pre_authorization_message_blocks = messages.get_pre_authorization_message(
        user_name, fyle_oauth_url
    )
    return {"type": "home", "blocks": pre_authorization_message_blocks}


def get_post_authorization_message() -> Dict:
    post_authorization_message_blocks = messages.get_post_authorization_message()
    return {"type": "home", "blocks": post_authorization_message_blocks}


def generate_category_field_mapping(expense_fields):
    mapping = {}
    for ef in expense_fields:
        # for ci in ef['org_category_ids']:
        # 	if ci not in mapping:
        # 		mapping[ci] = []
        # 	if not any(ef['column_name'] in cd for cd in mapping[ci]):
        # 		ci_details = {
        # 			'field_name': ef['field_name'],
        # 			'column_name': ef['column_name'],
        # 			'type': ef['type'],
        # 			'is_custom': ef['is_custom'],
        # 			'is_enabled': ef['is_enabled'],
        # 			'is_mandatory': ef['is_mandatory'],
        # 			'placeholder': ef['placeholder'],
        # 			'default_value': ef['default_value'],
        # 			'category_ids': ef['org_category_ids']
        # 		}
        # 		if ef['type'] == 'SELECT':
        # 			ci_details['options'] = ef['options']
        # 		mapping[ci].append(ci_details)

        if ef["column_name"] not in mapping:
            mapping[ef["column_name"]] = []

        ci_details = {
            "field_name": ef["field_name"],
            "column_name": ef["column_name"],
            "type": ef["type"],
            "is_custom": ef["is_custom"],
            "is_enabled": ef["is_enabled"],
            "is_mandatory": ef["is_mandatory"],
            "placeholder": ef["placeholder"],
            "default_value": ef["default_value"],
            "category_ids": ef["org_category_ids"],
        }
        if ef["type"] in ["SELECT", "MULTI_SELECT"]:
            ci_details["options"] = ef["options"]
        mapping[ef["column_name"]].append(ci_details)

    return mapping


def expense_dialog_form(extra_fields=None):
    # blocks = []
    # mappings = generate_category_field_mapping(expense_fields)
    # for expense_field in expense_fields:
    #     if expense_field["type"] in ["NUMBER", "TEXT"]:
    #         block = {
    #             "type": "input",
    #             # "block_id": "{}".format(random),
    #             "label": {
    #                 "type": "plain_text",
    #                 "text": "{}".format(expense_field["field_name"]),
    #             },
    #             "element": {
    #                 "type": "plain_text_input",
    #                 "action_id": "{}".format(expense_field["field_name"].lower()),
    #                 "placeholder": {
    #                     "type": "plain_text",
    #                     "text": "{}".format(expense_field["placeholder"]),
    #                 },
    #             },
    #         }
    #     elif expense_field["type"] == "SELECT":
    #         block = {
    #             "type": "input",
    #             # "block_id": "{}".format(uuid.uuid4()),
    #             "label": {
    #                 "type": "plain_text",
    #                 "text": "{}".format(expense_field["field_name"]),
    #             },
    #             "element": {
    #                 "type": "static_select",
    #                 "action_id": "{}".format(expense_field["field_name"].lower()),
    #                 "placeholder": {
    #                     "type": "plain_text",
    #                     "text": "{}".format(expense_field["placeholder"]),
    #                 },
    #                 "options": [
    #                     {
    #                         "text": {
    #                             "type": "plain_text",
    #                             "text": "*this is plain_text text*",
    #                         },
    #                         "value": "value-0",
    #                     },
    #                     {
    #                         "text": {
    #                             "type": "plain_text",
    #                             "text": "*this is plain_text text*",
    #                         },
    #                         "value": "value-1",
    #                     },
    #                     {
    #                         "text": {
    #                             "type": "plain_text",
    #                             "text": "*this is plain_text text*",
    #                         },
    #                         "value": "value-2",
    #                     },
    #                 ],
    #             },
    #         }

    #     blocks.append(block)
    current_date = datetime.datetime.today().strftime("%Y-%m-%d")
    cf_category = {"id": 136250, "name": "Custom Field Category"}
    internet_category = {"id": 136518, "name": "Internet"}
    os_category = {"id": 1234, "name": "Office Supplies"}
    view = {
        "type": "modal",
        "callback_id": "create_expense",
        "title": {"type": "plain_text", "text": "Create Expense", "emoji": True},
        "submit": {"type": "plain_text", "text": "Add Expense", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "type": "input",
                "block_id": "currency_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select Currency",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "INR",
                                "emoji": True,
                            },
                            "value": "INR",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "USD",
                                "emoji": True,
                            },
                            "value": "USD",
                        },
                    ],
                    "action_id": "currency",
                },
                "label": {"type": "plain_text", "text": "Currency", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "amount_block",
                "element": {
                    "type": "plain_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter Amount",
                        "emoji": True,
                    },
                    "action_id": "amount",
                },
                "label": {"type": "plain_text", "text": "Amount", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "payment_mode_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select Payment Mode",
                        "emoji": True,
                    },
                    "initial_option": {
                        "text": {
                            "type": "plain_text",
                            "text": "Paid by me",
                            "emoji": True,
                        },
                        "value": "paid_by_me",
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Paid by me",
                                "emoji": True,
                            },
                            "value": "paid_by_me",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Paid by company",
                                "emoji": True,
                            },
                            "value": "paid_by_company",
                        },
                    ],
                    "action_id": "payment_mode",
                },
                "label": {"type": "plain_text", "text": "Payment Mode", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "purpose_block",
                "element": {
                    "type": "plain_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Eg. Client Meeting",
                        "emoji": True,
                    },
                    "action_id": "purpose",
                },
                "label": {"type": "plain_text", "text": "Purpose", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "date_of_spend_block",
                "element": {
                    "type": "datepicker",
                    "initial_date": current_date,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date",
                        "emoji": True,
                    },
                    "action_id": "spent_at",
                },
                "label": {"type": "plain_text", "text": "Date of Spend", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "merchant_block",
                "element": {
                    "type": "plain_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Eg. Uber",
                        "emoji": True,
                    },
                    "action_id": "merchant",
                },
                "label": {"type": "plain_text", "text": "Merchant", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "category_block",
                "dispatch_action": True,
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Eg. Travel",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Custom Field Category",
                                "emoji": True,
                            },
                            "value": "136250",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Internet",
                                "emoji": True,
                            },
                            "value": "136518",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Office Supplies",
                                "emoji": True,
                            },
                            "value": "1234",
                        },
                    ],
                    "action_id": "category",
                },
                "label": {"type": "plain_text", "text": "Category", "emoji": True},
            },
        ],
    }
    # view = {
    #     "type": "modal",
    #     "callback_id": "create_expense",
    #     "title": {"type": "plain_text", "text": "Add Expense"},
    #     "submit": {"type": "plain_text", "text": "Add Expense"},
    #     "close": {"type": "plain_text", "text": "Cancel"},
    #     "notify_on_close": False,
    #     "blocks": blocks,
    # 	# "private_metadata": zlib.compress(base64.b64encode(json.dumps(mappings).encode())).decode()
    # }
    if extra_fields is not None:
        for field in extra_fields:
            if field["type"] in ["NUMBER", "TEXT"]:
                fld = {
                    "type": "input",
                    "block_id": "custom_field_{}_block".format(field["column_name"]),
                    "label": {
                        "type": "plain_text",
                        "text": "{}".format(field["field_name"]),
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "{}".format(field["field_name"]),
                        "placeholder": {
                            "type": "plain_text",
                            "text": "{}".format(field["placeholder"]),
                        },
                    },
                }
            elif field["type"] in ["SELECT", "MULTI_SELECT"]:
                if field["type"] == "SELECT":
                    field_type = "static_select"
                elif field["type"] == "MULTI_SELECT":
                    field_type = "multi_static_select"
                fld = {
                    "type": "input",
                    "label": {
                        "type": "plain_text",
                        "text": "{}".format(field["field_name"]),
                        "emoji": True,
                    },
                    "block_id": "custom_field_{}_block".format(field["column_name"]),
                    "element": {
                        "type": field_type,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "{}".format(field["placeholder"]),
                            "emoji": True,
                        },
                        "action_id": "{}".format(field["field_name"]),
                    },
                }
                fld["element"]["options"] = []
                for option in field["options"]:
                    fld["element"]["options"].append(
                        {
                            "text": {
                                "type": "plain_text",
                                "text": option,
                                "emoji": True,
                            },
                            "value": option,
                        }
                    )
            elif field["type"] == "BOOLEAN":
                fld = {
                    "type": "input",
                    "block_id": "custom_field_{}_block".format(field["column_name"]),
                    "optional": True,
                    "element": {
                        "type": "checkboxes",
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "{}".format(field["field_name"]),
                                    "emoji": True,
                                }
                            }
                        ],
                        "action_id": "{}".format(field["field_name"]),
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "{}".format(field["field_name"]),
                        "emoji": True,
                    },
                }
            view["blocks"].append(fld)

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
