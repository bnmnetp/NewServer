# ******************************************
# runestone/|docname| - The Runestone module
# ******************************************
# .. toctree::
#   :glob:
#
#   api/__init__.py
#   book_server/__init__.py
#   *.py
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
from flask import Flask
from config import config

# Local imports
# -------------
from .extensions import db, bootstrap, mail
from .model import user_manager


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    user_manager.init_app(app)

    # TODO: Why put these here?
    from runestone.book_server.server import book_server
    from runestone.api.endpoints import api
    app.register_blueprint(book_server)
    app.register_blueprint(api)

    return app
