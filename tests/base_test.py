# *****************************************
# |docname| - Base class for all unit tests
# *****************************************
# This provides the fixtures and a base class to simplify unit tests.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
from urllib.parse import urlencode
import json

# Third-party imports
# -------------------
import pytest
from flask import url_for

# Local imports
# -------------
from runestone import create_app

# Tests
# =====
# Create a testing application.
app = create_app('testing')


# Utilities
# ---------
# Create a URL based on a prefix (defined by a blueprint), an optional string (appended to the prefix), and any arguments (as keywords) to accompany a GET or POST request.
def url_joiner(url_prefix, _str, **kwargs):
    return '?'.join( (url_prefix + '/' + _str, urlencode(dict(kwargs))) )


# Define a `context manger <https://docs.python.org/3/reference/datamodel.html#context-managers>`_ which sandwiches its body with a ``login``/``logout``.
class LoginContext:
    def __init__(self, test_class, username, *args):
        self.test_class = test_class
        self.username = username
        self.args = args

    def __enter__(self):
        return self.test_class.login(self.username, *self.args)

    def __exit__(self, exc_type, exc_value, traceback):
        self.test_class.logout()


# Execute an HTTP verb, verifying the results. Return the response. On failure, write the resulting HTML to ``tmp.html``.
def check_verb(
    # A function to execute an HTTP verb -- a method of `test.Client <http://werkzeug.pocoo.org/docs/0.12/test/#werkzeug.test.Client>`_ and `TestClient <http://flask.pocoo.org/docs/0.12/api/#test-client>`_. For example, ``test_client.get``.
    verb_func,
    # _`url`: The bare URL to reqeust (so that ``/`` refers to the root of the web site).
    url,
    # _`expected_status`: The expected `status code <http://flask.pocoo.org/docs/0.11/api/#flask.Response.status_code>`_ returned by the web server. See https://en.wikipedia.org/wiki/List_of_HTTP_status_codes for a list of all codes.
    expected_status,
    # _`expected_response_phrase`: A phrase which must be ``in`` the text returned. The type must be ``bytes``; the default argument of ``b''`` skips this check.
    expected_response_phrase=b'',
    # _`kwargs`: Any additional keyword arguments to pass to `test_client.get <http://werkzeug.pocoo.org/docs/0.11/test/#werkzeug.test.Client.get>`_, such as ``follow_redirects=True``.
    **kwargs):

    # The call to an HTTP verb returns a `response object <http://flask.pocoo.org/docs/0.11/api/#response-objects>`_.
    rv = verb_func(url, **kwargs)
    try:
        # Check the `status code`_ and the `data <http://flask.pocoo.org/docs/0.11/api/#flask.Response.data>`_.
        assert rv.status_code == expected_status
        assert expected_response_phrase in rv.data
    except AssertionError:
        # On a test failure, save the resulting web page for debug purposes.
        with open('tmp.html', 'wb') as f:
            f.write(rv.data)
        raise
    return rv


# Given a query which returns a table/class, convert it returned columns to dicts, removing all ``args`` from it.
def result_remove(query, *args):
    result = []
    # Always remove SQLAlchemy internals.
    args = list(args) + ['_sa_instance_state']
    for _ in query:
        d = _.__dict__
        for key in args:
            del d[key]
        result.append(d)
    return result


# Apply these fixes to every test `automatically <https://docs.pytest.org/en/latest/fixture.html#using-fixtures-from-classes-modules-or-projects>`_.
@pytest.mark.usefixtures("test_client_")
# Group everything in a class, so it's easy to share the ``test_client``.
class BaseTest:
    # Create a fixture which stores the test_client in ``self``.
    @pytest.fixture()
    def test_client_(self, test_client):
        self.test_client = test_client
        self.username = 'brad@test.user'
        self.login_context = LoginContext(self, self.username, 'grouplens')

    # _`get_check`: Get a web page, checking its returned status code and optionally its contents.
    def get_check(self,
        # See `url`_.
        url,
        # See `expected_status`_.
        expected_status,
        # See `expected_response_phrase`_.
        expected_response_phrase=b'',
        # See `kwargs`_.
        **kwargs):

        # Use to `test_client.get`_ verb.
        return check_verb(self.test_client.get, url, expected_status, expected_response_phrase, **kwargs)

    def post_check(self,
        # See `url`_.
        url,
        # See `expected_status`_.
        expected_status,
        # See `expected_response_phrase`_.
        expected_response_phrase=b'',
        # See `kwargs`_.
        **kwargs):

        # Use to `test_client.get`_ verb.
        return check_verb(self.test_client.post, url, expected_status, expected_response_phrase, **kwargs)

    # _`get_valid`: Get a web page, verifying the `status code`_ was 200 (OK). This function returns the value produced by get_check_.
    def get_valid(self,
        # See url_.
        url,
        # Optionally provide the expected_response_phrase_.
        *args,
        # See kwargs_.
        **kwargs):

        return self.get_check(url, 200, *args, **kwargs)

    # After get_valid_, check that the returned data is the expected, JSON-formatted dict. This function returns the value produced by get_valid_.
    def get_valid_json(self,
        # See url_.
        url,
        # The expected response dictionary produce by interpreting the response data as UTF-8 encoded JSON.
        expected_response_dict,
        # See kwargs_.
        **kwargs):

        rv = self.get_valid(url, **kwargs)
        assert json.loads(str(rv.data, encoding='utf-8')) == expected_response_dict
        return rv

    # Get a web page, verifying the `status code`_ was 404 (not found). This function returns the value produced by get_check_.
    def get_invalid(self,
        # See url_.
        url,
        # See kwargs_.
        **kwargs):

        return self.get_check(url, 404, b'The requested URL was not found on the server.',
            **kwargs)

    # Verify that a login with the given username succeeds.
    def login(self, username, password):
        rv = self.post_check(url_for('user.login'), 200, data=dict(
                username=username,
                password=password,
                next=url_for(app.config['USER_AFTER_LOGIN_ENDPOINT']),
            ),
            follow_redirects=True)
        ##assert b'You have signed in successfully.' in rv.data
        return rv

    # Verify that a logout succeeds.
    def logout(self):
        return self.get_valid(app.config['USER_LOGOUT_URL'],
            b'You have signed out successfully.', follow_redirects=True)

    def must_login(self, url):
        self.logout()
        return self.get_valid(url, b'You must be signed in to access', follow_redirects=True)
