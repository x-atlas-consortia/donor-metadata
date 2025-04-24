"""
Routines to support calls to REST APIs subject to throttling or timeout.
Employs a retry loop.
Can be invoked from within either a Flask app or in a script.
If this will ever be called from a script, the import of flask does not apply.

"""
import requests

# For retry loop
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from flask import abort, current_app

def getresponsejson(url: str, method: str, headers=None, json=None) -> dict:
    """
    Obtains a response from a REST API.
    Employs a retry loop in case of timeout or other failures.

    :param url: the URL to the REST API
    :param method: GET or POST
    :param headers: optional headers
    :param json: optional response body for POST
    :return:
    """

    # Use the HTTPAdapter's retry strategy, as described here:
    # https://oxylabs.io/blog/python-requests-retry

    # Five retries max.
    # A backoff factor of 2, which results in exponential increases in delays before each attempt.
    # Retry for scenarios such as Service Unavailable or Too Many Requests that often are returned in case
    # of an overloaded server.
    try:
        retry = Retry(
            total=10,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retry)

        session = requests.Session()
        session.mount('https://', adapter)
        # r = session.get('https://httpbin.org/status/502', timeout=180)
        if method == 'GET':
            r = session.get(url=url, timeout=180)
        else:
            r = session.post(url=url, timeout=180, headers=headers, json=json)

        return r.json()

    except Exception as e:
        print(f'Error with URL {url}, json={json}: {e}')
        if current_app is not None:
            abort(500)
        else:
            raise(e)