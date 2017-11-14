# *****************************
# |docname| - run a test server
# *****************************
import os
from runestone import create_app, db
from runestone.model import Auth_User

app = create_app(os.getenv('FLASK_CONFIG') or 'testing')


def make_user(app, username, password):
    u = Auth_User[username].q
    if not u.count():
        user = Auth_User(
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
