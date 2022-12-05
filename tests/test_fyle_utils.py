import os
from fyle_slack_app.fyle import utils as fyle_utils
from django.conf import settings
from requests import Response
import mock
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class TestUtils:
    def test_get_fyle_sdk_connection(self, mocker, db):
        refresh_token = os.environ['FYLE_REFRESH_TOKEN']
        connection = fyle_utils.get_fyle_sdk_connection(refresh_token)
        assert  connection._Platform__client_id == os.environ['FYLE_CLIENT_ID'] and \
                connection._Platform__client_secret == os.environ['FYLE_CLIENT_SECRET'] 

    def test_is_receipt_file_supported(self):
        file_info = {
            'file':{
                'filetype': 'docx',
                'size': 2*1024*1024
            }
        }
        is_receipt_supported, response_message  = fyle_utils.is_receipt_file_supported(file_info=file_info)
        assert not is_receipt_supported and response_message == 'Invalid file type, please upload JPG, JPEG, PNG, or PDF'

        file_info = {
            'file':{
                'filetype': 'jpg',
                'size': 0
            }
        }
        is_receipt_supported, response_message  = fyle_utils.is_receipt_file_supported(file_info=file_info)
        assert not is_receipt_supported and response_message == 'Please upload file sizes greater than 0KB' 

        file_info = {
            'file':{
                'filetype':'jpg',
                'size':6*1024*1024
            }
        }
        is_receipt_supported, response_message  = fyle_utils.is_receipt_file_supported(file_info=file_info)
        assert not is_receipt_supported and response_message == 'Please upload file sizes lesser than 5MB' 

        file_info = {
            'file':{
                'filetype':'jpg',
                'size':3*1024*1024
            }
        }
        is_receipt_supported, response_message  = fyle_utils.is_receipt_file_supported(file_info=file_info)
        assert is_receipt_supported

    def test_extract_expense_from_receipt(self, mocker, db):
        fake_receipt_payload, refresh_token = {}, os.environ['FYLE_REFRESH_TOKEN']
        mock_response = mock.Mock(spec = Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': 'Running Fine',
            'cluster_domain': '{}/oauth/cluster'.format(settings.FYLE_ACCOUNTS_URL)
        }
        mocker.patch('fyle_slack_app.libs.http.post', return_value=mock_response)
        is_extracted = fyle_utils.extract_expense_from_receipt(fake_receipt_payload, refresh_token)
        assert is_extracted=='Running Fine'

    def test_get_fyle_refresh_token(self, mocker):
        mock_response = mock.Mock(spec = Response)
        mock_response.status_code = 200
        REFRESH_TOKEN = os.environ['FYLE_REFRESH_TOKEN']
        mock_response.json.return_value = {
            'data': 'Running Fine',
            'refresh_token': REFRESH_TOKEN
        }
        mocker.patch('fyle_slack_app.libs.http.post', return_value=mock_response)
        returned_refresh_token = fyle_utils.get_fyle_refresh_token('fake-code')
        assert returned_refresh_token == REFRESH_TOKEN

    def test_get_fyle_resource_url(self):
        fyle_refresh_token = os.environ['FYLE_REFRESH_TOKEN']
        resource, resource_type = {
            'name':'fake-image',
            'id': 'fake_id',
            'org_id': 'fake-org-id'
        }, 'REPORT'
        fyle_resource_url = fyle_utils.get_fyle_resource_url(fyle_refresh_token, resource, resource_type)
        assert fyle_resource_url == r'https://fyle.app.link/branchio_redirect?redirect_uri=https%3A%2F%2Fapp.fyle.tech%2Fapp%2Fmain%2F%23%2Freports%2Ffake_id?org_id=fake-org-id'

    def test_get_fyle_oauth_url(self):
        FAKE_USER_ID, FAKE_TEAM_ID = 'fake-user-id', 'fake-team-id'
        fake_fyle_oauth_url = fyle_utils.get_fyle_oauth_url(FAKE_USER_ID, FAKE_TEAM_ID)
        validator = URLValidator()
        try:
            validator(fake_fyle_oauth_url)
        except ValidationError:
            assert False

    def test_create_receipt(self, mocker):
        REFRESH_TOKEN = os.environ['FYLE_REFRESH_TOKEN']
        FAKE_PAYLOAD = {
            'data':'value'
        }
        mock_response = mock.Mock(spec = Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': FAKE_PAYLOAD,
            'cluster_domain': fyle_utils.get_cluster_domain(REFRESH_TOKEN) 
        }
        mocker.patch('fyle_slack_app.libs.http.post', return_value=mock_response)
        returned_payload = fyle_utils.create_receipt(FAKE_PAYLOAD, REFRESH_TOKEN)
        assert returned_payload == FAKE_PAYLOAD

    def test_generate_receipt_url(self, mocker):
        FAKE_RECEIPT_ID, REFRESH_TOKEN = 'fake-receipt-id', os.environ['FYLE_REFRESH_TOKEN']
        mock_response = mock.Mock(spec = Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': FAKE_RECEIPT_ID
            },
            'cluster_domain': fyle_utils.get_cluster_domain(REFRESH_TOKEN) 
        }
        mocker.patch('fyle_slack_app.libs.http.post', return_value=mock_response)
        json_response = fyle_utils.generate_receipt_url(FAKE_RECEIPT_ID, REFRESH_TOKEN)
        assert json_response['id'] == FAKE_RECEIPT_ID

    def test_attach_receipt_to_expense(self, mocker):
        FAKE_EXPENSE_ID = 'fake-expense-id'
        FAKE_RECEIPT_ID, REFRESH_TOKEN = 'fake-receipt-id', os.environ['FYLE_REFRESH_TOKEN']
        mock_response = mock.Mock(spec = Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': FAKE_EXPENSE_ID,
                'file_id' : FAKE_RECEIPT_ID
            },
            'cluster_domain': fyle_utils.get_cluster_domain(REFRESH_TOKEN) 
        }
        mocker.patch('fyle_slack_app.libs.http.post', return_value=mock_response)
        json_response = fyle_utils.attach_receipt_to_expense(FAKE_EXPENSE_ID, FAKE_RECEIPT_ID, REFRESH_TOKEN)
        assert json_response['file_id'] == FAKE_RECEIPT_ID and json_response['id'] == FAKE_EXPENSE_ID

    def test_upload_file_to_s3(self, mocker):
        mock_response = mock.Mock(spec = Response)
        mock_response.status_code = 200
        mocker.patch('fyle_slack_app.libs.http.put', return_value=mock_response)
        FAKE_UPLOAD_URL, FAKE_FILE_CONTENT , CONTENT_TYPE = 'https://fake-url.com', 'fake-file-content', 'json'
        response = fyle_utils.upload_file_to_s3(FAKE_UPLOAD_URL, FAKE_FILE_CONTENT , CONTENT_TYPE)
        assert response.status_code == 200
