import os
import unittest
import httpretty
import json

from time import sleep, time

from ..client import (
    iNaturalistClient
)

def register_token_url():
    httpretty.register_uri(
        httpretty.POST, "https://www.inaturalist.org/oauth/token",
        body=json.dumps({"auth_token": "what are you token about?"})
    )

class TestiNaturalistAuth(unittest.TestCase):

    @httpretty.activate
    def test_get_token(self):
        register_token_url()

        inaturalist = iNaturalistClient("user", "1234", "a client id", "its a secret")
        assert inaturalist.token is None

        inaturalist._get_new_token()
        assert inaturalist.token == "what are you token about?"
        assert inaturalist.auth_headers == {"Authorization": "Bearer what are you token about?"}

        assert dict(httpretty.last_request().body) == {
            "username": "user",
            "password": "1234",
            "client_id": "a client id",
            "client_secret": "its a secret",
            "grant_type": "password"
        }

    @httpretty.activate
    def test_need_new_token(self):
        register_token_url()

        inaturalist = iNaturalistClient(
            "user", "1234", "a client id", "its a secret", time_to_stale=1
        )
        assert inaturalist._need_new_token()

        inaturalist._get_new_token()
        assert not inaturalist._need_new_token()

        sleep(1)

        assert inaturalist._need_new_token()

    @httpretty.activate
    def test_update_app_url(self):
        app_url = 'http://my_cool_url/'
        httpretty.register_uri(
            httpretty.POST, "http://my_cool_url/oauth/token",
            body=json.dumps({"auth_token": "what are you token about?"})
        )

        inaturalist = iNaturalistClient(
            "user", "1234", "a client id", "its a secret", app_url=app_url
        )
        assert inaturalist.token is None

        inaturalist._get_new_token()
        assert inaturalist.token == "what are you token about?"
        assert inaturalist.auth_headers == {"Authorization": "Bearer what are you token about?"}
