from typing import Dict

from fyle.platform.platform import Platform

from fyle_slack_app.models.users import User
from fyle_slack_app.fyle import utils as fyle_utils

class FyleCorporateCard:

    connection: Platform = None

    def __init__(self, user: User) -> None:
        self.connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)


    def get_corporate_card_by_id(self, corporate_card_id: str) -> Dict:
        query_params = {
            'id': 'eq.{}'.format(corporate_card_id),
            'order': 'created_at.desc',
            'limit': '1',
            'offset': '0'
        }
        response = self.connection.v1beta.spender.corporate_cards.list(query_params=query_params)
        corporate_card = response['data'] if response['count'] == 1 else None
        return corporate_card

    def get_corporate_card_transaction(self, corporate_card_id: str) -> Dict:
        query_params = {
            'id': 'eq.{}'.format(corporate_card_id),
            'order': 'created_at.desc',
            'limit': '1',
            'offset': '0'
        }
        response = self.connection.v1beta.admin.corporate_card_transactions.list(query_params=query_params)
        corporate_card_transaction = response['data'][0]
        return corporate_card_transaction