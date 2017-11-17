# *****************************************************************************
# |docname| - define the tables necessary for serving textbooks, api and logins
# *****************************************************************************
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
from sqlalchemy import DateTime, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
import sqlalchemy.types as types
from flask_user import UserMixin, UserManager, SQLAlchemyAdapter
from gluon.validators import CRYPT

# Local imports
# -------------
from runestone import db

# Web2Py boolean type
# ===================
# Define a web2py-compatible Boolean type. See `custom types <http://docs.sqlalchemy.org/en/latest/core/custom_types.html>`_.
class Web2PyBoolean(types.TypeDecorator):
    impl = types.CHAR(1)

    def process_bind_param(self, value, dialect):
        if value:
            return 'T'
        elif value is None:
            return None
        elif not value:
            return 'F'
        else:
            assert False

    def process_result_value(self, value, dialect):
        if value == 'T':
            return True
        elif value == 'F':
            return False
        elif value is None:
            return None
        else:
            assert False

    def copy(self, **kw):
        return Web2PyBoolean(self.impl.length)

# Models
# ======
class Courses(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String, unique=True)
    term_start_date = db.Column(db.Date)
    base_course = db.Column(db.String, db.ForeignKey('courses.course_name'))
    python3 = db.Column(Web2PyBoolean)
    login_required = db.Column(Web2PyBoolean)

    # Create ``child_courses`` which all refer to a single ``parent_course``: children's ``base_course`` matches a parent's ``course_name``. See `adjacency list relationships <http://docs.sqlalchemy.org/en/latest/orm/self_referential.html#self-referential>`_.
    child_courses = db.relationship('Courses', backref=backref('parent_course', remote_side=[course_name]))

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.course_name == key

# Regex to convert web2py to SQLAlchemy - Field\('(\w+)',\s*'(\w+)'\), --> $1 = db.Column(db.$2)
class UseInfo(db.Model):
    __tablename__ = 'useinfo'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    sid = db.Column(db.String)
    event = db.Column(db.String)
    act = db.Column(db.String)
    div_id = db.Column(db.String)
    course_id = db.Column(db.String)

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.sid == key

class Auth_User(db.Model, UserMixin):
    __tablename__ = 'auth_user'
    id = Column(Integer, primary_key=True)
    username = Column(String(512), nullable=False, unique=True)
    first_name = Column(String(512))
    last_name = Column(String(512))
    email = Column(String(512), unique=True)
    password = Column(String(512))
    created_on = Column(DateTime())
    modified_on = Column(DateTime())
    registration_key = Column(String(512))
    reset_password_key = Column(String(512))
    registration_id = Column(String(512))
    cohort_id = Column(String(512))
    course_id = Column(String(512))
    active = Column(Web2PyBoolean)

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.username == key

# Flask-User customization
# ========================
# This can't be placed in `extensions.py`, because it needs the ``User`` model to be defined.
#
# Use's web2py's encryption. See http://flask-user.readthedocs.io/en/v0.6/customization.html#password-hashing.
class UserManagerWeb2Py(UserManager):
    def init_app(self, app):
        super().init_app(app)

        # Create the web2py encrypter.
        self.crypt = CRYPT(key=app.config['WEB2PY_PRIVATE_KEY'], salt=app.config['WEB2PY_SALT'])

    def hash_password(self, password):
        return str(self.crypt(password)[0])

    def verify_password(self, password, user):
        return self.hash_password(password) == self.get_password(user)

db_adapter = SQLAlchemyAdapter(db, Auth_User)
user_manager = UserManagerWeb2Py(db_adapter)
