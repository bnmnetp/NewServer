# ****************************************
# |docname| - Fixture shared by unit tests
# ****************************************
# This provides fixtures which simplify unit tests.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
# None

# Third-party imports
# -------------------
import pytest

# Local imports
# -------------
from runestone import db
from runestone.model import AuthUser

# Data
# ----
# Create a user if they don't exist, or return the existing user.
def make_user(app, username, password):
    u = db.session.AuthUser[username].q
    if not u.count():
        user = AuthUser(
            username=username,
            password=app.user_manager.hash_password(password),
        )
        db.session.add(user)
        db.session.commit()
    else:
        user = u.one()
    return user

# Creates some fake data which the tests use.
def create_test_data(app):
    make_user(app, 'brad@test.user', 'grouplens')
    db.session.commit()

# Fixtures
# ========
# Set up the database for the test session. Do this just once for all tests, rather than every test (module scope).
@pytest.fixture(scope='module')
def test_db(request):
    app = request.module.app
    # _`test_client`: the `test client <http://flask.pocoo.org/docs/0.11/api/#flask.Flask.test_client>`_ to request pages from.
    test_client = app.test_client()
    with app.app_context():
        db.create_all()

    return test_client

# Define `per-function setup and teardown <http://doc.pytest.org/en/latest/fixture.html#fixture-finalization-executing-teardown-code>`_ which places test data in an already existing database, then removes all data from the database when the test finishes.
@pytest.fixture()
def test_client(test_db, request):
    # Setup
    app = request.module.app
    with app.app_context():
        create_test_data(app)

    def teardown():
        with app.app_context():
            # Teardown. Adapted from http://stackoverflow.com/a/5003705. A simple db.drop_all() works, but doubles test time. This should remove all data, but keep the schema.
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()
    request.addfinalizer(teardown)

    return test_db
