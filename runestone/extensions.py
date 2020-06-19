# ************************************
# |docname| - Initialize Flask plugins
# ************************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
# None
#
# Third-party imports
# -------------------
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from pythonic_sqlalchemy_query.flask import SQLAlchemyPythonicQuery

# Local imports
# -------------
# None
#
# Create extensions
# =================
bootstrap = Bootstrap()
db = SQLAlchemyPythonicQuery()
mail = Mail()
