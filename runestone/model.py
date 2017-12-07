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
from sqlalchemy.ext.declarative import declared_attr
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
# Important: per the `docs <http://flask-sqlalchemy.pocoo.org/2.3/models/>`_, table names are derived from the class name; a class of ``CamelCase`` is converted to a table name of ``camel_case``.
#
# TODO: Document the meaning of every field. Document the relationships.
#
# Regex to convert web2py to SQLAlchemy - Field\('(\w+)',\s*'(\w+)'\), --> $1 = db.Column(db.$2).
#
# IdMixin
# -------
# Always name a table's ID field the same way.
class IdMixin:
    id = db.Column(db.Integer, primary_key=True)


# AuthUser
# --------
# This matches Web2Py's fields, and also works with Flask-User.
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


# Courses
# -------
# Defines either a base course (which must be manually added to the database) or a derived course created by an instructor.
class Courses(db.Model, IdMixin):
    # _`course_name`: The name of this course.
    course_name = db.Column(db.String(512), unique=True)
    term_start_date = db.Column(db.Date)
    # TODO: Why not use base_course_id instead? _`base_course`: the course from which this course was derived. TODO: If this is a base course, this field should be identical to the course_name_?
    base_course = db.Column(db.String(512), db.ForeignKey('courses.course_name'))
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


# Useinfo
# -------
# User info logged by the `hsblog endpoint`. See there for more info.
class Useinfo(db.Model, IdMixin):
    # _`timestamp`: when this entry was recorded by this webapp.
    timestamp = db.Column(db.DateTime)
    # _`sid`: TODO: The student id? (user) which produced this row.
    sid = db.Column(db.String(512))
    # The type of question (timed exam, fill in the blank, etc.).
    event = db.Column(db.String(512))
    # TODO: What is this? The action associated with this log entry?
    act = db.Column(db.String(512))
    # _`div_id`: the ID of the question which produced this entry.
    div_id = db.Column(db.String(512))
    # _`course_id`: the Courses ``course_name`` **NOT** the ``id`` this row refers to. TODO: Use the ``id`` instead!
    course_id = db.Column(db.String(512), db.ForeignKey('courses.course_name'))

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.sid == key


# Questions
# ---------
# A question in the book; this data is provided by Sphinx.
class Questions(db.Model, IdMixin):
    # The base_course_ this question is in.
    base_course = db.Column(db.String(512), nullable=False)
    # The div_id_ for this question. TODO: Rename this!
    name = db.Column(db.String(512), nullable=False)
    # matches chapter_label, not name
    chapter = db.Column(db.String(512))
    # matches sub_chapter_label, not name
    subchapter = db.Column(db.String(512))
    author = db.Column(db.String(512))
    difficulty = db.Column(db.Integer)
    question = db.Column(db.Text)
    timestamp = db.Column(db.DateTime),
    question_type = db.Column(db.String(512))
    is_private = db.Column(Web2PyBoolean)
    htmlsrc = db.Column(db.Text)
    autograde = db.Column(db.String(512))

    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.name == key


# Answers to specific question types
# ----------------------------------
# Many of the tables containing answers are always accessed by sid, div_id and course_name. Provide this as a default query. TODO: Obviously, this is poor database design -- there should be a single key, rather than using all three as a key. Refactor.
class AnswerMixin(IdMixin):
    # TODO: these entries duplicate Useinfo.timestamp. Why not just have a timestamp_id field?
    #
    # See timestamp_.
    timestamp = db.Column(db.DateTime)
    # See div_id_.
    div_id = db.Column(db.String(512))
    # See sid_.
    sid = db.Column(db.String(512))

    # See course_name_. Mixins with foreign keys need `special treatment <http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/mixins.html#mixing-in-columns>`_.
    @declared_attr
    def course_name(cls):
        return db.Column(db.String(512), db.ForeignKey('courses.course_name'))

    @classmethod
    def default_query(cls, key):
        if isinstance(key, tuple):
            sid, div_id, course_name = key
            return (cls.sid == sid) and (cls.div_id == div_id) and (course_name == course_name)


class TimedExam(db.Model, AnswerMixin):
    # See the `timed exam endpoint parameters <timed exam>` for documenation on these columns.
    correct = db.Column(db.Integer)
    incorrect = db.Column(db.Integer)
    skipped = db.Column(db.Integer)
    time_taken = db.Column(db.Integer)
    # True if the ``act`` endpoint parameter was ``'reset'``; otherwise, False.
    reset = db.Column(Web2PyBoolean)

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.sid == key


# Like an AnswerMixin, but also has a boolean correct_ field.
class CorrectAnswerMixin(AnswerMixin):
    # _`correct`: True if this answer is correct.
    correct = db.Column(Web2PyBoolean)

    @classmethod
    def default_query(cls, key):
        if isinstance(key, bool):
            return key == cls.correct
        else:
            return super().default_query(key)


# An answer to a multiple-choice question.
class MchoiceAnswers(db.Model, CorrectAnswerMixin):
    # _`answer`: The answer to this question. TODO: what is the format?
    answer = db.Column(db.String(50))


# An answer to a fill-in-the-blank question.
class FitbAnswers(db.Model, CorrectAnswerMixin):
    # See answer_. TODO: what is the format?
    answer = db.Column(db.String(512))


# An answer to a drag-and-drop question.
class DragndropAnswers(db.Model, CorrectAnswerMixin):
    # See answer_. TODO: what is the format?
    answer = db.Column(db.String(512))


# An answer to a drag-and-drop question.
class ClickableareaAnswers(db.Model, CorrectAnswerMixin):
    # See answer_. TODO: what is the format?
    answer = db.Column(db.String(512))


# An answer to a Parsons problem.
class ParsonsAnswers(db.Model, CorrectAnswerMixin):
    # See answer_. TODO: what is the format?
    answer = db.Column(db.String(512))
    # _`source`: The source code provided by a student? TODO.
    source = db.Column(db.String(512))


# An answer to a Code Lens problem.
class CodelensAnswers(db.Model, CorrectAnswerMixin):
    # See answer_. TODO: what is the format?
    answer = db.Column(db.String(512))
    # See source_.
    source = db.Column(db.String(512))


class ShortanswerAnswers(db.Model, AnswerMixin):
    # See answer_. TODO: what is the format?
    answer = db.Column(db.String(512))


# Flask-User customization
# ========================
# This can't be placed in `extensions.py`, because it needs the AuthUser_ model to be defined.
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
