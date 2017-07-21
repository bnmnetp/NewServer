from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bootstrap import Bootstrap
from flask_security import Security, SQLAlchemySessionUserDatastore
from .extensions import db, bootstrap, security, mail
from .model import User, Role


user_datastore = SQLAlchemySessionUserDatastore(db.session,
                                                User, Role)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)
    mail.init_app(app)


    security.init_app(app, user_datastore)    

    from runestone.book_server.server import book_server
    app.register_blueprint(book_server)

    return app
