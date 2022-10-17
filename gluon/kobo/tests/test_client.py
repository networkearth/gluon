import os
import unittest
import httpretty
import json

from time import sleep, time

from ..client import (
    KoboClient
)

def register_token_url():
    httpretty.register_uri(
        httpretty.GET, "https://kf.kobotoolbox.org/token?format=json",
        body=json.dumps({"token": "what are you token about?"})
    )

class TestKoboAuth(unittest.TestCase):

    @httpretty.activate
    def test_get_token(self):
        register_token_url()

        kobo = KoboClient("user", "1234")
        assert kobo.token is None

        kobo._get_new_token()
        assert kobo.token == "what are you token about?"
        assert kobo.auth_headers == {"Authorization": "Token what are you token about?"}

        assert dict(httpretty.last_request().headers)["Authorization"].startswith("Basic")

    @httpretty.activate
    def test_need_new_token(self):
        register_token_url()

        kobo = KoboClient("user", "1234", time_to_stale=1)
        assert kobo._need_new_token()

        kobo._get_new_token()
        assert not kobo._need_new_token()

        sleep(1)

        assert kobo._need_new_token()

    @httpretty.activate
    def test_ensure_authorized(self):
        register_token_url()

        httpretty.register_uri(
            httpretty.GET, "https://kf.kobotoolbox.org/api/v2/assets/5678/data.json",
            body=json.dumps({"results": "stuff"})
        )

        kobo = KoboClient("user", "1234", time_to_stale=1)
        assert kobo.token_refresh_time == -float("inf")
        assert kobo.token is None

        kobo.pull_data("5678")
        assert kobo.token_refresh_time > -float("inf")
        assert kobo.token is not None

        last_token_refresh_time = kobo.token_refresh_time

        sleep(1)

        kobo.pull_data("5678")
        assert kobo.token_refresh_time > last_token_refresh_time

        assert dict(httpretty.last_request().headers)["Authorization"] == "Token what are you token about?"

class TestPulls(unittest.TestCase):
    @httpretty.activate
    def test_pull_data(self):
        register_token_url()
        
        httpretty.register_uri(
            httpretty.GET, "https://kf.kobotoolbox.org/api/v2/assets/5678/data.json",
            body=json.dumps({"results": ["some", "data"]})
        )

        kobo = KoboClient("user", "1234")

        data = kobo.pull_data("5678")
        assert data == ["some", "data"]

        assert dict(httpretty.last_request().headers)["Authorization"] == "Token what are you token about?"

    @httpretty.activate
    def test_pull_image(self):
        register_token_url()

        httpretty.register_uri(
            httpretty.GET, "https://kf.kobotoolbox.org/api/v2/assets/5678/data/9/attachments/0/",
            body="a pretty picture"
        )

        kobo = KoboClient("user", "1234")

        file_path = f'{int(time())}_test_pull_image.png'

        try:
            kobo.pull_image(file_path, "5678", "9", "0")
            with open(file_path, 'rb') as fh:
                content = fh.read().decode('utf-8')
        except Exception as e:
            os.remove(file_path)
            raise e
        os.remove(file_path)

        assert content == "a pretty picture"

        assert dict(httpretty.last_request().headers)["Authorization"] == "Token what are you token about?"
