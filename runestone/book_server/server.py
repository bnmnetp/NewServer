import os, os.path
from flask import Blueprint, render_template, send_from_directory, request, redirect
from flask_security import login_required


from ..model import Course

# Why a blueprint? I think what's needed is:
#
# - Which course was required.
# - The base course from which this course was created.
#
# Then, simply fill in the eBookConfig and that's it. The base course can be found by querying the db based on the given course. Cache this if performance is a problem.
book_server = Blueprint('book_server',__name__, template_folder='templates', url_prefix='/runestone')

@book_server.route('/')
@login_required
def hello_world():
    return 'Hello World! {}'.format(os.getcwd())

@book_server.route('/<path:course>/_static/<path:filename>')
@book_server.route('/<path:course>/_images/<path:filename>')
def custom_static(course, filename):
    '''
    We have to efficiently serve all of the assets, this seems a common way to do so.
    There is some mention of `X-sendfile header <http://flask.pocoo.org/docs/0.12/api/#flask.send_from_directory>`_ along with send_file and this should be investigated. See also the `howto <http://pythonhosted.org/xsendfile/howto.html>`_.

    Other possibly helpful links:

    -   https://www.digitalocean.com/community/tutorials/how-to-deploy-python-wsgi-apps-using-gunicorn-http-server-behind-nginx
    -   http://talhaoz.com/2014/07/serving-files-with-flask-behind-nginx-gunicorn/

    :param course:
    :param filename:
    :return:
    '''
    path = os.path.join(os.getcwd(),'runestone', 'book_server', 'templates', 'thinkcspy','_static')
    #book_server.logger.debug(request.url)
    return send_from_directory(path, filename)

@login_required
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

    #book_server.logger.debug(pageinfo)

    base_course = the_course.base_course
    course_version = '3'
    python3 = 'true' if the_course.python3 == 'T' else 'false'
    login_required = 'true' if the_course.login_required == 'T' else 'false'

    template = os.path.join(base_course, pageinfo)
    return render_template(template, basecourse=base_course, python3=python3, login_required=login_required)

