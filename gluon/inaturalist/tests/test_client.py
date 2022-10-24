import unittest
import httpretty
import json
import os

from time import sleep

from ..client import (
    iNaturalistClient
)

def register_token_url():
    httpretty.register_uri(
        httpretty.POST, "https://www.inaturalist.org/oauth/token",
        body=json.dumps({"access_token": "what are you token about?"})
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

        assert json.loads(httpretty.last_request().body) == {
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
            body=json.dumps({"access_token": "what are you token about?"})
        )

        inaturalist = iNaturalistClient(
            "user", "1234", "a client id", "its a secret", app_url=app_url
        )
        assert inaturalist.token is None

        inaturalist._get_new_token()
        assert inaturalist.token == "what are you token about?"
        assert inaturalist.auth_headers == {"Authorization": "Bearer what are you token about?"}

class TestiNaturalistObservation(unittest.TestCase):

    @httpretty.activate
    def test_upload_base_observation(self):
        register_token_url()
        httpretty.register_uri(
            httpretty.POST, "https://www.inaturalist.org/v1/observations",
            body=json.dumps({"id": 11})
        )

        inaturalist = iNaturalistClient(
            "user", "1234", "a client id", "its a secret"
        )
        observation_id = inaturalist.upload_base_observation(
            2, -71.157109, 42.462211, 
            "2022-08-17T10:04:00-04:00", 
            5, "Hello World!"
        )
        assert "Authorization: Bearer what are you token about?" in str(httpretty.last_request().headers)
        assert json.loads(httpretty.last_request().body) == {
            "observation": {
                "taxon_id": 2,
                "latitude": 42.462211,
                "longitude": -71.157109,
                "observed_on_string": "2022-08-17T10:04:00-04:00",
                "positional_accuracy": 5,
                "description": "Hello World!"
            }
        }
        assert observation_id == 11

    @httpretty.activate
    def test_attach_observation_field_value(self):
        register_token_url()
        httpretty.register_uri(
            httpretty.POST, "https://www.inaturalist.org/v1/observation_field_values",
            body=json.dumps({})
        )

        inaturalist = iNaturalistClient(
            "user", "1234", "a client id", "its a secret"
        )
        inaturalist.attach_observation_field(
            10, 1, "a field value"
        )
        
        assert "Authorization: Bearer what are you token about?" in str(httpretty.last_request().headers)
        assert json.loads(httpretty.last_request().body) == {
            "observation_field_value": {
                "observation_id": 10,
                "observation_field_id": 1,
                "value": "a field value"
            }
        }

    @httpretty.activate
    def test_attach_image(self):
        register_token_url()
        httpretty.register_uri(
            httpretty.POST, "https://www.inaturalist.org/v1/observation_photos",
            body=json.dumps({})
        )

        image_path = 'test_photo.png'
        with open(image_path, 'wb') as fh:
            fh.write(b'a flower I guess?')

        try:
            inaturalist = iNaturalistClient(
                "user", "1234", "a client id", "its a secret"
            )
            inaturalist.attach_image(
                10, image_path
            )
        except Exception as e:
            os.remove(image_path)
            raise e

        os.remove(image_path)
        
        assert "Authorization: Bearer what are you token about?" in str(httpretty.last_request().headers)
        assert (
            "\r\nContent-Disposition: form-data; name=\"observation_photo[observation_id]\"\r\n\r\n10\r\n" 
            in bytes(httpretty.last_request().body).decode('utf-8')
        )
        assert (
            "\r\nContent-Disposition: form-data; name=\"file\"; filename=\"test_photo.png\"\r\n\r\na flower I guess?\r\n"
        )
