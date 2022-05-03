from typing import Dict

from fyle.platform.platform import Platform

from fyle_slack_app.fyle.utils import get_fyle_sdk_connection
from fyle_slack_app.models.users import User


class FyleExpense:
    connection: Platform = None

    def __init__(self, user: User) -> None:
        self.connection = get_fyle_sdk_connection(user.fyle_refresh_token)


    def get_expense_by_id(self, expense_id: str) -> Dict:
        query_params = {
            'id': 'eq.{}'.format(expense_id),
            'order': 'created_at.desc',
            'limit': '1',
            'offset': '0'
        }
        response = self.connection.v1beta.spender.expenses.list(query_params=query_params)
        expense = response['data'] if response['count'] == 1 else None
        return expense
