# ********************************************
# |docname| - Configure this Flask application
# ********************************************
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Set the `secret_key <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.secret_key>`_ to enable `sessions <http://flask.pocoo.org/docs/0.12/api/#sessions>`_ in Flask. See `the note under sessions <http://flask.pocoo.org/docs/0.12/quickstart/#sessions>`_ for how to generate a good key.
    SECRET_KEY = 'top-secret'

    # Flask-SQLAlchemy
    #
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Web2py credentials
    #
    # The file ``web2py/applications/runestone/private/auth.key`` contains Web2py's private encryption key. Provide it as a string here.
    WEB2PY_PRIVATE_KEY = 'sha512:2c560062-762c-4399-a304-85658e363801'
    # web2py stores password in the format ``<algorithm>$<salt>$<hash>``. This is the salt value. To obtain this on Windows, ``psql %DBURL%`` then ``select * from auth_user;``. Provide it as a string.
    WEB2PY_SALT = 'b9d8e92d9e5d8882'

    # Flask-User
    #
    # Disable e-mail confirmation, since web2py doesn't do this. Also, this means we don't need a ``confirmed_at`` column, which would mean a database migration to add it.
    USER_ENABLE_CONFIRM_EMAIL = False
    # Used by email templates
    USER_APP_NAME = 'Runestone Interactive'
    USER_AFTER_LOGIN_ENDPOINT = 'book_server.hello_world'

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DBURL')

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('LIVE_DBURL')
    SECURITY_CONFIRMABLE = True
    MAIL_SERVER = None
    MAIL_PORT = None
    MAIL_USE_SSL = None
    MAIL_USERNAME = None
    MAIL_PASSWORD = None

class TestingConfig(Config):
    DEBUG = True

    # Use a testing-only database.
    #
    # While an in-membory SQLite test database is handy, it doesn't behave like a PostgreSQL database. Don't test on it.
    ##SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Instead, use a command like ``createdb --owner=<yournamehere> runestone_test`` (``"C:\Program Files\PostgreSQL\9.6\bin\createdb" --owner=<yournamehere> -U postgres runestone_test`` on Windows).
    SQLALCHEMY_DATABASE_URI = 'postgresql://web2py_db_instance:verysilly@localhost/runestone_test'
    # Propagate exceptions (don't show 500 error page). See `testing <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.testing>`_.
    TESTING = True
    # Disable CSRF token in Flask-Wtf.
    WTF_CSRF_ENABLED = False
    # Enable @register_required while app.testing=True.
    LOGIN_DISABLED = False
    # Suppress the sending of emails.
    MAIL_SUPPRESS_SEND = True
    # Enable url_for() without request context.
    SERVER_NAME = 'localhost'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}

