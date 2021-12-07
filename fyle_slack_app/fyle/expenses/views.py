from typing import Dict, List

import datetime

from fyle.platform.platform import Platform

from fyle_slack_app.fyle.utils import get_fyle_sdk_connection
from fyle_slack_app.libs.utils import decode_state, encode_state
from fyle_slack_app.models.users import User
from fyle_slack_app.fyle import utils as fyle_utils


class FyleExpense:

    connection: Platform = None

    def __init__(self, user: User) -> None:
        self.connection = get_fyle_sdk_connection(user.fyle_refresh_token)


    def get_expense_fields(self, query_params: Dict) -> Dict:
        return self.connection.v1beta.spender.expense_fields.list(query_params=query_params)


    def get_default_expense_fields(self) -> Dict:
        default_expense_fields_query_params = {
            'offset': 0,
            'limit': '50',
            'order': 'created_at.desc',
            'column_name': 'in.(purpose, txn_dt, vendor_id, cost_center_id, project_id)',
            'is_enabled': 'eq.{}'.format(True),
            'is_custom': 'eq.{}'.format(False)
        }

        return self.get_expense_fields(default_expense_fields_query_params)


    def get_custom_fields_by_category_id(self, category_id: str) -> Dict:
        custom_fields_query_params = {
            'offset': 0,
            'limit': '50',
            'order': 'created_at.desc',
            'column_name': 'not_in.(purpose, txn_dt, vendor_id, cost_center_id)',
            'is_enabled': 'eq.{}'.format(True),
            'category_ids': 'cs.[{}]'.format(int(category_id))
        }

        return self.get_expense_fields(custom_fields_query_params)


    def get_categories(self, query_params: Dict) -> Dict:
        return self.connection.v1beta.spender.categories.list(query_params=query_params)


    def get_projects(self, query_params: Dict) -> Dict:
        return self.connection.v1beta.spender.projects.list(query_params=query_params)


    def get_cost_centers(self, query_params: Dict) -> Dict:
        return self.connection.v1beta.spender.cost_centers.list(query_params=query_params)


    def get_expenses(self, query_params: Dict) -> Dict:
        return self.connection.v1beta.spender.expenses.list(query_params=query_params)


    def get_reports(self, query_params: Dict) -> Dict:
        return self.connection.v1beta.spender.reports.list(query_params=query_params)


    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Dict:
        current_date = datetime.datetime.today().strftime('%Y-%m-%d')
        exchange_rate = self.connection.v1beta.common.currencies_exchange_rate.get(
            from_currency, to_currency, current_date
        )
        return exchange_rate['data']['exchange_rate']


    def check_project_availability(self) -> bool:
        projects_query_params = {
            'offset': 0,
            'limit': '1',
            'order': 'created_at.desc',
            'is_enabled': 'eq.{}'.format(True)
        }

        projects = self.get_projects(projects_query_params)

        is_project_available = True if projects['count'] > 0 else False

        return is_project_available


    def check_cost_center_availability(self) -> bool:
        cost_centers_query_params = {
            'offset': 0,
            'limit': '1',
            'order': 'created_at.desc',
            'is_enabled': 'eq.{}'.format(True)
        }

        cost_centers = self.get_cost_centers(cost_centers_query_params)

        is_cost_center_available = True if cost_centers['count'] > 0 else False

        return is_cost_center_available


    @staticmethod
    def get_currencies():
        return ['ADP','AED','AFA','ALL','AMD','ANG','AOA','ARS','ATS','AUD','AWG','AZM','BAM','BBD','BDT','BEF','BGL','BGN','BHD','BIF','BMD','BND','BOB','BOV','BRL','BSD','BTN','BWP','BYB','BZD','CAD','CDF','CHF','CLF','CLP','CNY','COP','CRC','CUP','CVE','CYP','CZK','DEM','DJF','DKK','DOP','DZD','ECS','ECV','EEK','EGP','ERN','ESP','ETB','EUR','FIM','FJD','FKP','FRF','GBP','GEL','GHC','GIP','GMD','GNF','GRD','GTQ','GWP','GYD','HKD','HNL','HRK','HTG','HUF','IDE','IDR','IEP','ILS','INR','IQD','IRR','ISK','ITL','JMD','JOD','JPY','KES','KGS','KHR','KMF','KPW','KRW','KWD','KYD','KZT','LAK','LBP','LKR','LRD','LSL','LTL','LUF','LVL','LYD','MAD','MDL','MGF','MKD','MMK','MNT','MOP','MRO','MTL','MUR','MVR','MWK','MXN','MXV','MYR','MZM','NAD','NGN','NIO','NLG','NOK','NPR','NZD','OMR','PAB','PEN','PGK','PHP','PKR','PLN','PTE','PYG','QAR','ROL','RUB','RUR','RWF','RYR','SAR','SBD','SCR','SDP','SEK','SGD','SHP','SIT','SKK','SLL','SOS','SRG','STD','SVC','SYP','SZL','THB','TJR','TMM','TND','TOP','TPE','TRL','TTD','TWD','TZS','UAH','UGX','USD','USN','USS','UYU','UZS','VEB','VND','VUV','WST','XAF','XCD','XDR','XEU','XOF','XPF','YER','YUN','ZAR','ZMK','ZRN','ZWD']


    @staticmethod
    def get_expense_fields_mandatory_mapping(expense_fields: List[Dict]) -> Dict:
        mandatory_fields_mapping = {
            'purpose': False,
            'txn_dt': False,
            'vendor_id': False,
            'project_id': False,
            'cost_center_id': False
        }

        for field in expense_fields['data']:
            if field['column_name'] in mandatory_fields_mapping:
                mandatory_fields_mapping[field['column_name']] = field['is_mandatory']

        return mandatory_fields_mapping


    @staticmethod
    def get_expense_form_details(user: User) -> Dict:

        fyle_expense = FyleExpense(user)

        fyle_profile = fyle_utils.get_fyle_profile(user.fyle_refresh_token)

        home_currency = fyle_profile['org']['currency']

        default_expense_fields = fyle_expense.get_default_expense_fields()

        mandatory_fields_mapping = fyle_expense.get_expense_fields_mandatory_mapping(default_expense_fields)

        is_project_available = fyle_expense.check_project_availability()
        is_cost_center_available = fyle_expense.check_cost_center_availability()

        # Create a expense fields render property and set them optional in the form
        fields_render_property = {
            'project': {
                'is_project_available': is_project_available,
                'is_mandatory': mandatory_fields_mapping['project_id']
            },
            'cost_center': {
                'is_cost_center_available': is_cost_center_available,
                'is_mandatory': mandatory_fields_mapping['cost_center_id']
            },
            'purpose': mandatory_fields_mapping['purpose'],
            'transaction_date': mandatory_fields_mapping['txn_dt'],
            'vendor': mandatory_fields_mapping['vendor_id']
        }

        additional_currency_details = {
            'home_currency': home_currency
        }

        add_to_report = 'existing_report'

        # Caching details in slack private metadata so that they can be reused again in the form without computing them again
        private_metadata = {
            'fields_render_property': fields_render_property,
            'additional_currency_details': additional_currency_details,
            'add_to_report': add_to_report
        }

        expense_form_details = {
            'fields_render_property': fields_render_property,
            'private_metadata': encode_state(private_metadata),
            'additional_currency_details': additional_currency_details,
            'add_to_report': add_to_report
        }

        return expense_form_details


    @staticmethod
    def get_current_expense_form_details(slack_payload: Dict) -> Dict:

        private_metadata = slack_payload['view']['private_metadata']

        decoded_private_metadata = decode_state(private_metadata)

        fields_render_property = decoded_private_metadata['fields_render_property']

        additional_currency_details = decoded_private_metadata.get('additional_currency_details')

        add_to_report = decoded_private_metadata.get('add_to_report')

        current_ui_blocks = slack_payload['view']['blocks']

        project = decoded_private_metadata.get('project')

        custom_field_blocks = []

        for block in current_ui_blocks:
            if 'custom_field' in block['block_id'] or 'additional_field' in block['block_id']:
                custom_field_blocks.append(block)

        if len(custom_field_blocks) == 0:
            custom_field_blocks = None

        current_form_details = {
            'fields_render_property': fields_render_property,
            'selected_project': project,
            'additional_currency_details': additional_currency_details,
            'add_to_report': add_to_report,
            'private_metadata': private_metadata,
            'custom_fields': custom_field_blocks
        }
        return current_form_details
