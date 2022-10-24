import requests
from time import time, sleep

from ..utils import clean_url

class iNaturalistClient(object):
    def __init__(self, username: str, password: str, client_id: str, client_secret: str, **kwargs) -> None:
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret

        self.app_url = clean_url(
            kwargs.get('app_url', 'https://www.inaturalist.org')
        )
        self.api_url = clean_url(
            kwargs.get('api_url', 'https://api.inaturalist.org/v1')
        )
        self.time_to_stale = kwargs.get("time_to_stale", 300)
        self.time_between_requests = 1./kwargs.get('rate', float('inf'))

        self.token = None
        self.auth_headers = {}
        self.token_refresh_time = -float('inf')
        self.last_request_time = -float('inf')

    def _need_new_token(self) -> None:
        return time() - self.token_refresh_time >= self.time_to_stale

    def _get_new_token(self) -> None:
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }
        response = requests.post(
            f'{self.app_url}/oauth/token',
            json=payload
        )
        self.token = response.json()['access_token']
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        self.token_refresh_time = time()

    def ensure_authorized(method):
        def check_auth_then_run_method(self, *args, **kwargs):
            if self._need_new_token():
                self._get_new_token()
            return method(self, *args, **kwargs)

        return check_auth_then_run_method

    def rate_limit(method):
        def limit(self, *args, **kwargs):
            time_left = self.time_between_requests - (time() - self.last_request_time)
            sleep(max(time_left, 0))
            self.last_request_time = time()
            return method(self, *args, **kwargs)

        return limit

    @rate_limit
    @ensure_authorized
    def upload_base_observation(
        self, taxon_id: int, longitude: float, latitude: float, 
        observed_on_string: str, positional_accuracy: float, 
        description: str
    ) -> int:
        payload = {
            "observation": {
                "taxon_id": taxon_id,
                "longitude": longitude,
                "latitude": latitude,
                "observed_on_string": observed_on_string,
                "positional_accuracy": positional_accuracy,
                "description": description
            }   
        }
        response = requests.post(
            f'{self.api_url}/observations',
            headers=self.auth_headers,
            json=payload
        )
        return response.json()['id']

    @rate_limit
    @ensure_authorized
    def attach_image(
        self, observation_id: int, file_path: str
    ) -> None:
        form_data = {
            "file": (file_path, open(file_path, 'rb')),
            "observation_photo[observation_id]": (None, observation_id)
        }
        response = requests.post(
            f'{self.api_url}/observation_photos',
            headers=self.auth_headers,
            files=form_data
        )

    @rate_limit
    @ensure_authorized
    def attach_observation_field(
        self, observation_id: int, observation_field_id: int, value
    ) -> None:
        payload = {
            "observation_field_value": {
                "observation_id": observation_id,
                "observation_field_id": observation_field_id,
                "value": value
            }
        }
        response = requests.post(
            f'{self.api_url}/observation_field_values',
            headers=self.auth_headers,
            json=payload
        )
