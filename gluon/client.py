class Client(object):
    def ensure_authorized(method):
        def check_auth_then_run_method(self, *args, **kwargs):
            if self._need_new_token():
                self._get_new_token()
            return method(self, *args, **kwargs)

        return check_auth_then_run_method