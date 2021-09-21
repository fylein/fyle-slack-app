from typing import Dict

from fyle_slack_app.fyle.utils import get_fyle_sdk_connection
from fyle_slack_app.models.users import User


class FyleExpense:

    @staticmethod
    def get_expense_fields(user: User, query_params: Dict) -> Dict:
        connection = get_fyle_sdk_connection(user.fyle_refresh_token)
        expense_fields = connection.v1.fyler.expense_fields.list(query_params=query_params)
        return expense_fields


    @staticmethod
    def get_default_expense_fields(user: User) -> Dict:
        default_expense_fields_query_params = {
            'offset': 0,
            'limit': '20',
            'order': 'created_at.desc',
            'column_name': 'in.(purpose, txn_dt, vendor_id, cost_center_id, project_id)',
            'is_enabled': 'eq.{}'.format(True),
            'is_custom': 'eq.{}'.format(False),
            'is_mandatory': 'eq.{}'.format(True)
        }

        default_expense_fields = FyleExpense.get_expense_fields(user, default_expense_fields_query_params)

        return default_expense_fields



    @staticmethod
    def get_categories(user: User, query_params: Dict) -> Dict:
        connection = get_fyle_sdk_connection(user.fyle_refresh_token)
        categories = connection.v1.fyler.categories.list(query_params=query_params)
        return categories


    @staticmethod
    def get_projects(user: User, query_params: Dict) -> Dict:
        connection = get_fyle_sdk_connection(user.fyle_refresh_token)
        projects = connection.v1.fyler.projects.list(query_params=query_params)
        return projects
