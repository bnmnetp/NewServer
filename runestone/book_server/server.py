from flask import Blueprint, render_template, send_from_directory, request, redirect
import os.path

from runestone import app
from ..model import Course


book_server = Blueprint('book_server',__name__, template_folder='templates', url_prefix='/runestone')

@book_server.route('/')
def hello_world():
    return 'Hello World!'

@book_server.route('/<path:course>/_static/<path:filename>')
@book_server.route('/<path:course>/_images/<path:filename>')
def custom_static(course, filename):
    '''
    We have to efficiently serve all of the assets, this seems a common way to do so.
    There is some mention of X-sendfile header along with send_file and this should be investigated
    :param course:
    :param filename:
    :return:
    '''
    path = '/Users/bmiller/Runestone/server/runestone/book_server/templates/thinkcspy/_static'
    app.logger.debug(request.url)
    return send_from_directory(path, filename)

@book_server.route('/<string:course>/<path:pageinfo>')
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
    
    base_course = the_course.base_course
    course_version = '3'
    python3 = 'true' if the_course.python3 == 'T' else 'false'
    login_required = 'true' if the_course.login_required == 'T' else 'false'

    template = os.path.join(base_course, pageinfo)
    return render_template(template, basecourse=base_course, python3=python3, login_required=login_required)

