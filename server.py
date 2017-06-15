from flask import Flask, render_template, send_from_directory, request
from course import get_base, get_version
import logging
import os.path

app = Flask(__name__)

rslogger = logging.getLogger('runestone.dev')
rslogger.setLevel('DEBUG')

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
    path = 'templates/thinkcspy/_static'
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
    app.logger.debug(pageinfo)
    app.logger.debug(request.url)
    base_course = get_base(course)
    course_version = get_version(course)
    python3 = True
    login_required = True

    template = os.path.join(base_course, pageinfo)
    return render_template(template, context=dict(basecourse=base_course, python3=python3, loginrequired=login_required))




if __name__ == '__main__':
    app.run(debug=True)
