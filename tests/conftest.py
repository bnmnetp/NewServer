# ****************************************
# |docname| - Fixture shared by unit tests
# ****************************************
# This provides pytest `fixtures <https://docs.pytest.org/en/latest/fixture.html>`_ which simplify unit tests.
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
from runestone.model import AuthUser, Courses, Questions


# Data
# ----
# Create a user if they don't exist, or return the existing user.
def make_user(app, username, password):
    u = AuthUser[username].q
    if not u.count():
        user = AuthUser(
            username=username,
            password=app.user_manager.hash_password(password),
            active=True,
        )
        db.session.add(user)
        db.session.commit()
    else:
        user = u.one()
    return user


# Creates some fake data which the tests use.
def create_test_data(app):
    # A test user.
    make_user(app, 'brad@test.user', 'grouplens')

    # Test courses.
    test_base_course = Courses(
        course_name='test_base_course',
        python3=True,
        login_required=True,
    )
    test_child_course1 = Courses(
        course_name='test_child_course1',
        parent_course=test_base_course,
        python3=True,
        login_required=True,
    )
    test_child_course2 = Courses(
        course_name='test_child_course2',
        parent_course=test_base_course,
        python3=False,
        login_required=False,
    )
    db.session.add(test_base_course)

    # A test question.
    db.session.add(Questions(
        base_course=test_base_course.course_name,
        name='test_div_id',
        chapter='1',
        subchapter='2',
    ))

    db.session.commit()


# Fixtures
# ========
# Define `per-function setup and teardown <http://doc.pytest.org/en/latest/fixture.html#fixture-finalization-executing-teardown-code>`_ which places test data in an empty database, then removes all data from the database when the test finishes.
#
# Note: http://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites describes another approach, which seems more complex, so I'm not using it.
@pytest.fixture()
def test_client(request):
    # Setup
    app = request.module.app

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    # Set up the database. In case something went wrong last test, drop everything first.
    db.drop_all()
    db.create_all()
    create_test_data(app)

    def teardown():
        # Without a commit or rollback, PostgreSQL will `hang <https://stackoverflow.com/questions/13882407/sqlalchemy-blocked-on-dropping-tables>`_. Using a rollback cleans up if a transaction was rejected by the backend database.
        db.session.rollback()
        db.drop_all()
        ctx.pop()
    request.addfinalizer(teardown)

    # A `test client <http://flask.pocoo.org/docs/0.11/api/#flask.Flask.test_client>`_ to request pages from.
    return app.test_client()
