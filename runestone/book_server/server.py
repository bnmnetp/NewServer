# ***************************
# |docname| - The core server
# ***************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
import os
from pathlib import Path

# Third-party imports
# -------------------
from flask import (
    Blueprint, render_template, send_from_directory, safe_join, redirect,
    current_app,
)
from flask_user import login_required, is_authenticated

# Local imports
# -------------
from ..model import Courses

# Blueprint
# =========
book_server = Blueprint('book_server', __name__, template_folder='templates', url_prefix='/runestone')


# Endpoints
# =========
# Just for testing. Mostly useless.
@book_server.route('/')
@login_required
def hello_world():
    return 'Hello World! {}<br><a href="/user/sign-out">Log out</a>'.format(os.getcwd())


# Transform a Boolean into a JavaScript string.
def js_bool(b):
    return str(bool(b)).lower()


# Book router
# ===========
# This routines all request for book pages to the appropriate file.
@book_server.route('/<string:course>/<path:pageinfo>')
def serve_page(course, pageinfo):
    '''
    Lookup information and fill in template information in eBookConfig.  Specifically:
    -   loginRequired
    -   Python3
    -   base course

    :param course: The name of the course
    :param pageinfo: the path to the page that is desired to be served
    :return: filled page template
    '''
    # Use the handy `query <http://flask-sqlalchemy.pocoo.org/2.3/queries/#querying-records>`_ attribute.
    the_course = Courses[course].q.first()
    if not the_course:
        return redirect(f'http://runestone/errors/nocourse/{course}')
    base_course = the_course.base_course
    filesystem_path = safe_join(base_course, pageinfo)

    # Enforce is_login_required.
    is_login_required = the_course.login_required
    if is_login_required and not is_authenticated():
        # Redirect to unauthenticated page
        return current_app.user_manager.unauthenticated_view_function()

    # See if this is static content in the book.
    if Path(pageinfo).parts[0] in ('_static', '_images'):
        # We have to efficiently serve all of the assets, this seems a common way to do so.
        # There is some mention of `X-sendfile header <http://flask.pocoo.org/docs/0.12/api/#flask.send_from_directory>`_ along with send_file and this should be investigated. See also the `howto <http://pythonhosted.org/xsendfile/howto.html>`_.
        #
        # Other possibly helpful links:
        #
        # -   https://www.digitalocean.com/community/tutorials/how-to-deploy-python-wsgi-apps-using-gunicorn-http-server-behind-nginx
        # -   http://talhaoz.com/2014/07/serving-files-with-flask-behind-nginx-gunicorn/
        #
        # Book static files are inside the templates/ folder, so build this path manually.
        templates_path = str(Path(book_server.root_path) / book_server.template_folder)
        return send_from_directory(templates_path, filesystem_path)
    else:
        python3_js = js_bool(the_course.python3)

        return render_template(filesystem_path, basecourse=base_course, python3=python3_js, login_required=js_bool(is_login_required))
