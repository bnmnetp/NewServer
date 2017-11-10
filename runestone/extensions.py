# ************************************
# |docname| - Initialize Flask plugins
# ************************************
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_mail import Mail

# Now create instances of our extension objects
bootstrap = Bootstrap()
db = SQLAlchemy()
security = Security()
mail = Mail()
