from typing import Any, Callable, Dict, Tuple

import json
import requests

from fyle_slack_app.libs import logger


logger = logger.get_logger(__name__)


def http_request(method: str, url: str, headers: Dict = None, **kwargs: Any) -> requests.Response:
    headers = requests.structures.CaseInsensitiveDict(headers)

    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        **kwargs
    )

    return resp


def process_data_and_headers(data: Dict, headers: Dict) -> Tuple[Dict, Dict]:
    headers = requests.structures.CaseInsensitiveDict(headers)

    if isinstance(data, dict):
        data = json.dumps(data)
        headers['Content-Type'] = 'application/json'

    return data, headers


def post(url: str, data: Dict = None, headers: Dict = None, **kwargs: Any) -> Callable:
    data, headers = process_data_and_headers(data, headers)
    return http_request('POST', url, headers=headers, data=data, **kwargs)


def put(url: str, data: Dict = None, headers: Dict = None, **kwargs: Any) -> Callable:
    data, headers = process_data_and_headers(data, headers)
    return http_request('PUT', url, headers=headers, data=data, **kwargs)


def get(url: str, *args: Any, **kwargs: Any) -> Callable:
    kwargs.setdefault('allow_redirects', True)
    return http_request('GET', url, **kwargs)


def delete(url: str, *args: Any, **kwargs: Any) -> Callable:
    return http_request('DELETE', url, **kwargs)
