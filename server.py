from flask import Flask, render_template, send_from_directory, request, redirect
from course import get_base, get_version
import logging
import os.path
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://millbr02:@localhost/runestone'
db = SQLAlchemy(app)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String, unique=True)
    term_start_date = db.Column(db.Date)
    base_course = db.Column(db.String)
    python3 = db.Column(db.Boolean)
    login_required = db.Column(db.Boolean)

db.create_all()


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/runestone/<path:course>/_static/<path:filename>')
def custom_static(course, filename):
    '''
    We have to efficiently serve all of the assests, this seems a common way to do so.
    :param course:
    :param filename:
    :return:
    '''
    path = os.path.join('templates', 'thinkcspy', '_static')
    return send_from_directory(path, filename)

@app.route('/runestone/<string:course>/<path:pageinfo>')
def serve_page(course, pageinfo):
    '''
    Lookup information and fill in template information in eBookConfig.  Specifically:
    - loginRequired
    - Python3
    - base course

    :param course: The name of the course
    :param pageinfo: the path to the page that is desired to be served
    :return: filled page template
    '''
    the_course = Course.query.filter_by(course_name=course).first()
    if not the_course:
        return redirect(f'http://runestone/errors/nocourse/{course}')

    app.logger.debug(pageinfo)
    app.logger.debug(type(the_course.python3))
    base_course = the_course.base_course
    course_version = get_version(course)
    python3 = 'true' if the_course.python3 == 'T' else 'false'
    login_required = 'true' if the_course.login_required == 'T' else 'false'

    template = os.path.join(base_course, pageinfo)
    return render_template(template, basecourse=base_course, python3=python3, login_required=login_required)



if __name__ == '__main__':
    app.run(debug=True)
