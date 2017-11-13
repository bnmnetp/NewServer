# *****************************************************************************
# |docname| - define the tables necessary for serving textbooks, api and logins
# *****************************************************************************
from sqlalchemy import Boolean, DateTime, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from flask_user import UserMixin, UserManager, SQLAlchemyAdapter
from gluon.validators import CRYPT

from runestone import db

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String, unique=True)
    term_start_date = db.Column(db.Date)
    base_course = db.Column(db.String)
    python3 = db.Column(db.Boolean)
    login_required = db.Column(db.Boolean)

# Regex to convert web2py to SQLAlchemy - Field\('(\w+)',\s*'(\w+)'\), --> $1 = db.Column(db.$2)
class LogInfo(db.Model):
    __tablename__ = 'useinfo'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    sid = db.Column(db.String)
    event = db.Column(db.String)
    act = db.Column(db.String)
    div_id = db.Column(db.String)
    course_id = db.Column(db.String)

class AuthUser(db.Model, UserMixin):
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
    active = Column(Boolean())

    # Define a default query: the username if provided a string. Otherwise, automatically fall back to the id.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.username == key

# Flask-User customization
# ========================
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
