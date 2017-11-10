import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'top-secret'
    SECURITY_REGISTERABLE = True
    SECURITY_PASSWORD_SALT = '7a183de0-7cdc-4132-966b-69bfac9f47a3'
    SECURITY_TRACKABLE = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DBURL')
    SECURITY_CONFIRMABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_POST_LOGIN_VIEW = '/runestone/'
    SECURITY_POST_LOGOUT_VIEW = '/runestone/'

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
    SECURITY_CONFIRMABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_POST_LOGIN_VIEW = '/runestone/'
    SECURITY_POST_LOGOUT_VIEW = '/runestone/'

    # In-memory sqlite DB
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Propagate exceptions (don't show 500 error page).
    TESTING = True
    # Disable CSRF token in Flask-Wtf.
    WTF_CSRF_ENABLED = False
    # Enable @register_required while app.testing=True.
    LOGIN_DISABLED = False
    # Suppress the sending of emails.
    MAIL_SUPPRESS_SEND = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}

