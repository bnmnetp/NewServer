# *****************************************************************************
# |docname| - define the tables necessary for serving textbooks, api and logins
# *****************************************************************************
from runestone import db
from sqlalchemy import Boolean, DateTime, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from flask_security import UserMixin, RoleMixin

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

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = Column(db.Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user_store.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))

class User(db.Model, UserMixin):
    __tablename__ = 'user_store'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('role', lazy='dynamic')) # was users but seems wrong.
