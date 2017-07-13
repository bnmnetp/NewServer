
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
    timestamp = db.Column(db.Datetime)
    sid = db.Column(db.String)
    event = db.Column(db.String)
    act = db.Column(db.String)
    div_id = db.Column(db.String)
    course_id = db.Column(db.String)

db.create_all()
