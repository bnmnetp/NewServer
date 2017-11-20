# *****************************
# |docname| - run a test server
# *****************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
import os

# Third-party imports
# -------------------
# None.

# Local imports
# -------------
from runestone import create_app, db
from runestone.model import AuthUser

# Create application
# ==================
app = create_app(os.getenv('FLASK_CONFIG') or 'development')


# TODO: This is duplicated in `tests/conftest.py`. Factor it out.
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


# Create a user to test with
@app.before_first_request
def create_user():
    db.create_all()

    make_user(app, 'brad@test.user', 'grouplens')
    db.session.commit()


# Main
# ====
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
