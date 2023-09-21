# Nautobot SDK

The repository lives here: <https://github.com/nautobot/pynautobot>

To remove SSL Certificate Verification:

Add the following line to the api.py file located in pynautobot\core\api.py after the Session object

~~~python
self.http_session.verify = False
~~~

It will look like this:

~~~python
def __init__(
        self,
        url,
        token=None,
        threading=False,
        api_version=None,
        retries=0,
    ):
        base_url = "{}/api".format(url if url[-1] != "/" else url[:-1])
        self.token = token
        self.headers = {"Authorization": f"Token {self.token}"}
        self.base_url = base_url
        self.http_session = requests.Session()
        self.http_session.verify = False
~~~
