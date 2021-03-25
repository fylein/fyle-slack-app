import json
import requests

from fyle_slack_app.libs import logger


logger = logger.get_logger(__name__)


def http_request(method, url, headers=None, **kwargs):
    headers = requests.structures.CaseInsensitiveDict(headers)

    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        **kwargs
    )

    return resp


def process_data_and_headers(data, headers):
    headers = requests.structures.CaseInsensitiveDict(headers)

    if isinstance(data, dict):
        data = json.dumps(data)
        headers['Content-Type'] = 'application/json'

    return data, headers


def post(url, data=None, headers=None, **kwargs):
    data, headers = process_data_and_headers(data, headers)
    return http_request('POST', url, headers=headers, data=data, **kwargs)


def put(url, data=None, headers=None, **kwargs):
    data, headers = process_data_and_headers(data, headers)
    return http_request('PUT', url, headers=headers, data=data, **kwargs)


def get(url, *args, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return http_request('GET', url, **kwargs)


def delete(url, *args, **kwargs):
    return http_request('DELETE', url, **kwargs)
