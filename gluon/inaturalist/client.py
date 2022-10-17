import requests
from time import time

from ..client import Client
from ..utils import clean_url

class iNaturalistClient(Client):
    def __init__(self, username: str, password: str, client_id: str, client_secret: str, **kwargs) -> None:
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret

        self.app_url = clean_url(
            kwargs.get('app_url', 'https://www.inaturalist.org')
        )
        self.api_url = clean_url(
            kwargs.get('api_url', 'https://www.inaturalist.org/v1')
        )
        self.time_to_stale = kwargs.get("time_to_stale", 300)

        self.token = None
        self.auth_headers = {}
        self.token_refresh_time = -float('inf')

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
            f'{self.app_url}/oauth/token'
        )
        self.token = response.json()['auth_token']
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        self.token_refresh_time = time()
