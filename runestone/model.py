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
from sqlalchemy.orm import backref
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
# TODO: Document the meaning of every field. Document the relationships.
#
# Regex to convert web2py to SQLAlchemy - Field\('(\w+)',\s*'(\w+)'\), --> $1 = db.Column(db.$2).

class IdMixin:
    id = db.Column(db.Integer, primary_key=True)

class Courses(db.Model, IdMixin):
    course_name = db.Column(db.String, unique=True)
    term_start_date = db.Column(db.Date)
    # TODO: Why not use base_course_id instead?
    base_course = db.Column(db.String, db.ForeignKey('courses.course_name'))
    # TODO: This should go in a different table. Not all courses have a Python/Skuplt component.
    python3 = db.Column(Web2PyBoolean)
    login_required = db.Column(Web2PyBoolean)

    # Create ``child_courses`` which all refer to a single ``parent_course``: children's ``base_course`` matches a parent's ``course_name``. See `adjacency list relationships <http://docs.sqlalchemy.org/en/latest/orm/self_referential.html#self-referential>`_.
    child_courses = db.relationship('Courses', backref=backref('parent_course', remote_side=[course_name]))

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.course_name == key


# User info logged by the `hsblog endpoint`. See there for more info.
class Useinfo(db.Model, IdMixin):
    # When this entry was recorded by this webapp.
    timestamp = db.Column(db.DateTime)
    # TODO: The student id? (user) which produced this row.
    sid = db.Column(db.String)
    # The type of question (timed exam, fill in the blank, etc.).
    event = db.Column(db.String)
    # TODO: What is this? The action associated with this log entry?
    act = db.Column(db.String)
    # The ID of the question which produced this entry.
    div_id = db.Column(db.String)
    # The Courses row this row refers to.
    course_id = db.Column(db.String, db.ForeignKey('courses.id'))

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.sid == key


class TimedExam(db.Model, IdMixin):
    # TODO: these entries duplicate Useinfo.timestamp. Why not just have a timestamp_id field?
    timestamp = db.Column(db.DateTime)
    div_id = db.Column(db.String(512))
    sid = db.Column(db.String(512))
    course_name = db.Column(db.String(512))
    correct = db.Column(db.Integer)
    incorrect = db.Column(db.Integer)
    skipped = db.Column(db.Integer)
    time_taken = db.Column(db.Integer)
    reset = db.Column(Web2PyBoolean)

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.sid == key


class AuthUser(db.Model, UserMixin, IdMixin):
    username = db.Column(db.String(512), nullable=False, unique=True)
    first_name = db.Column(db.String(512))
    last_name = db.Column(db.String(512))
    email = db.Column(db.String(512), unique=True)
    password = db.Column(db.String(512))
    created_on = db.Column(db.DateTime())
    modified_on = db.Column(db.DateTime())
    registration_key = db.Column(db.String(512))
    reset_password_key = db.Column(db.String(512))
    registration_id = db.Column(db.String(512))
    cohort_id = db.Column(db.String(512))
    course_id = db.Column(db.String(512))
    active = db.Column(Web2PyBoolean)

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.username == key


# Many of the tables containing answers are always accessed by sid, div_id and course_name. Provide this as a default query.
class AnswerQueryMixin(IdMixin):
    @classmethod
    def default_query(cls, key):
        if isinstance(key, tuple):
            sid, div_id, course_name = key
            return (cls.sid == sid) and (cls.div_id == div_id) and (course_name == course_name)


class MchoiceAnswers(db.Model, AnswerQueryMixin):
    pass
"""
db.define_table('mchoice_answers',
    Field('timestamp','datetime'),
    Field('div_id','string'),
    Field('sid','string'),
    Field('course_name','string'),
    Field('answer','string', length=50),
    Field('correct','boolean'),
"""

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

db_adapter = SQLAlchemyAdapter(db, AuthUser)
user_manager = UserManagerWeb2Py(db_adapter)
