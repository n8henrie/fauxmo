import requests


class RestApiHandler:
    """Rest API handler class.

    The Fauxmo class expects handlers to be instances of objects that have on()
    and off() methods that return True on success and False otherwise.  This
    example class takes two full URLs that should be requested when an on and
    off command are invoked respectively. It ignores any return data.
    """

    def __init__(self, on_cmd, off_cmd, method=None, json=None, headers=None):
        self.on_cmd = on_cmd
        self.off_cmd = off_cmd
        self.method = method
        self.json = json
        self.headers = headers

    def on(self):
        if self.method == "POST":
            r = requests.post(self.on_cmd, json=self.json,
                              headers=self.headers)
        else:
            r = requests.get(self.on_cmd, headers=self.headers)
        return r.status_code in [200, 201]

    def off(self):
        if self.method == "POST":
            r = requests.post(self.off_cmd, json=self.json,
                              headers=self.headers)
        else:
            r = requests.get(self.off_cmd, headers=self.headers)
        return r.status_code in [200, 201]
