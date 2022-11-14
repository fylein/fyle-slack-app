import json
from fyle_slack_app.libs.http import get, post, put, delete

BASE_URL = "https://httpbin.org"

class TestHTTPMethods:
    
    def test_get(self):
        URL = f"{BASE_URL}/get"
        resp = get(URL)
        assert resp.status_code == 200
        assert resp.json()['url'] == URL

    def test_post(self):
        URL = f"{BASE_URL}/post"
        resp = post(URL, data = json.dumps({
            "test":True,
            "source":"FYLE"
        }))
        assert resp.status_code == 200
        assert json.loads(resp.json()['data'])['source'] == "FYLE"

    def test_put(self):
        URL = f"{BASE_URL}/put"
        resp = put(URL, data = json.dumps({
            "test":True,
            "source":"FYLE"
        }))
        assert resp.status_code == 200
        assert json.loads(resp.json()['data'])['source'] == "FYLE"

    def test_delete(self):
        URL = f"{BASE_URL}/delete"
        resp = delete(URL)
        assert resp.status_code == 200
        assert resp.json()['data'] == ""