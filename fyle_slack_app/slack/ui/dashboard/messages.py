import json
from random import random
from typing import Dict

import random, copy

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


def generate_category_field_mapping(expense_fields):
	mapping = {}
	for ef in expense_fields:
		for ci in ef['org_category_ids']:
			if ci not in mapping:
				mapping[ci] = []
			ci_details = {
				'field_name': ef['field_name'],
				'type': ef['type'],
				'is_custom': ef['is_custom'],
				'is_enabled': ef['is_enabled'],
				'is_mandatory': ef['is_mandatory'],
				'placeholder': ef['placeholder'],
				'default_value': ef['default_value']
			}
			if ef['type'] == 'SELECT':
				ci_details['options'] = ef['options']
			mapping[ci].append(ci_details)

	print(json.dumps(mapping, indent=2))


def expense_dialog_form():
    blocks = []
    for expense_field in expense_fields:
        if expense_field["type"] in ["NUMBER", "TEXT"]:
            block = {
                "type": "input",
                # "block_id": "{}".format(random),
                "label": {
                    "type": "plain_text",
                    "text": "{}".format(expense_field["field_name"]),
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "{}".format(expense_field["field_name"].lower()),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "{}".format(expense_field["placeholder"]),
                    },
                },
            }
        elif expense_field["type"] == "SELECT":
            block = {
                "type": "input",
                # "block_id": "{}".format(uuid.uuid4()),
                "label": {
                    "type": "plain_text",
                    "text": "{}".format(expense_field["field_name"]),
                },
                "element": {
                    "type": "static_select",
                    "action_id": "{}".format(expense_field["field_name"].lower()),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "{}".format(expense_field["placeholder"]),
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "*this is plain_text text*",
                            },
                            "value": "value-0",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "*this is plain_text text*",
                            },
                            "value": "value-1",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "*this is plain_text text*",
                            },
                            "value": "value-2",
                        },
                    ],
                },
            }

        blocks.append(block)
    generate_category_field_mapping(expense_fields)
    view = {
        "type": "modal",
        "callback_id": "create_expense",
        "title": {"type": "plain_text", "text": "Add Expense"},
        "submit": {"type": "plain_text", "text": "Add Expense"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "notify_on_close": True,
        "blocks": blocks,
    }

    return view
