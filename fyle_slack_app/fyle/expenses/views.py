from typing import Dict, List
import datetime
from django.core.cache import cache
from fyle.platform.platform import Platform
from fyle_slack_app.fyle.utils import get_fyle_sdk_connection
from fyle_slack_app.models.users import User
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import assertions, http


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
        return self.connection.v1beta.spender.expenses.list(query_params=query_params)
