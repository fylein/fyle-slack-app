import json
from random import random
from typing import Dict

import random, copy, zlib, base64

from fyle_slack_app.slack.ui.authorization import messages


def get_pre_authorization_message(user_name: str, fyle_oauth_url: str) -> Dict:
    pre_authorization_message_blocks = messages.get_pre_authorization_message(
        user_name, fyle_oauth_url
    )
    return {"type": "home", "blocks": pre_authorization_message_blocks}


def get_post_authorization_message() -> Dict:
    post_authorization_message_blocks = messages.get_post_authorization_message()
    return {"type": "home", "blocks": post_authorization_message_blocks}


def mock_message():
    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "My App", "emoji": True},
        "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "dispatch_action": True,
                "type": "input",
                "element": {
                    "type": "external_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an item",
                        "emoji": True,
                    },
                    "action_id": "external_select_option",
                },
                "label": {"type": "plain_text", "text": "Label", "emoji": True},
            }
        ],
    }


def mock_message_2():
    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "My App", "emoji": True},
        "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "dispatch_action": True,
                "type": "input",
                "element": {
                    "type": "external_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an item",
                        "emoji": True,
                    },
                    "action_id": "external_select_option",
                },
                "label": {"type": "plain_text", "text": "Label", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Dynamic updated view",
                    "emoji": True,
                },
            },
        ],
    }


from fyle_slack_app.admin import expense_fields
from fyle_slack_app.libs.utils import encode_state


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
        if ef["type"] == "SELECT":
            ci_details["options"] = ef["options"]
        mapping[ef["column_name"]].append(ci_details)

    # print(json.dumps(mapping, indent=2))
    # print('MAPPINGS -> ', zlib.compress(base64.b64encode(json.dumps(mapping).encode())).decode())
    return mapping


def expense_dialog_form(extra_fields=None):
    blocks = []
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
    view = {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Create Expense", "emoji": True},
        "submit": {"type": "plain_text", "text": "Add Expense", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "type": "input",
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
                            "value": "inr",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "USD",
                                "emoji": True,
                            },
                            "value": "usd",
                        },
                    ],
                    "action_id": "category_select",
                },
                "label": {"type": "plain_text", "text": "Currency", "emoji": True},
            },
            {
                "type": "input",
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
                "element": {
                    "type": "datepicker",
                    "initial_date": "2021-08-23",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date",
                        "emoji": True,
                    },
                    "action_id": "datepicker-action",
                },
                "label": {"type": "plain_text", "text": "Date of Spend", "emoji": True},
            },
            {
                "type": "input",
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
                            "value": "123456",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Internet",
                                "emoji": True,
                            },
                            "value": "1234",
                        },
                    ],
                    "action_id": "category_select",
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
                    # "block_id": "{}".format(random),
                    "label": {
                        "type": "plain_text",
                        "text": "{}".format(field["field_name"]),
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "{}".format(field["field_name"].lower()),
                        "placeholder": {
                            "type": "plain_text",
                            "text": "{}".format(field["placeholder"]),
                        },
                    },
                }
                view["blocks"].append(fld)

    return view
