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

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    create_test_data(app)

    def teardown():
        # Teardown. Adapted from http://stackoverflow.com/a/5003705. A simple db.drop_all() works, but doubles test time. This should remove all data, but keep the schema.
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

        ctx.pop()
    request.addfinalizer(teardown)

    return test_db
