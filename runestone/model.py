
from runestone import db

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String, unique=True)
    term_start_date = db.Column(db.Date)
    base_course = db.Column(db.String)
    python3 = db.Column(db.Boolean)
    login_required = db.Column(db.Boolean)

db.create_all()
