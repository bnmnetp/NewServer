# *****************************
# |docname| - run a test server
# *****************************
import os
from runestone import create_app, db

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Create a user to test with
@app.before_first_request
def create_user():
    db.create_all()
    ##u = user_datastore.find_user(email='brad@test.user')
    ##if not u:
    ##    user_datastore.create_user(email='brad@test.user', password='grouplens')
    ##    db.session.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
