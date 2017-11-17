# ************************************************
# |docname| - provide Ajax endpoints used by books
# ************************************************
import uuid
from datetime import datetime
from flask import Blueprint, request, session, jsonify, current_app
from ..model import UseInfo, db
from flask_user import current_user, is_authenticated

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/hsblog')
def log_book_event():
    if is_authenticated():
        # ``current_user`` is a `proxy <https://flask-login.readthedocs.io/en/latest/#flask_login.current_user>`_ for the currently logged-in user. It returns ``None`` if no user is logged in.
        sid = current_user.username
        # If the user wasn't logged in, but is now, update all ``hsblog`` entries to their username. TODO: What about all the questions they answered? Are these in need up cascaded updates as well?
        if ('ipuser' in session) and (session['ipuser'] != sid):
            # Yes, so update all ``sid`` entries.
            for _ in UseInfo[sid]:
                _.sid = sid
    else:
        # Create a uuid for a user that's not logged in. See `request.cookies <http://flask.pocoo.org/docs/0.12/api/#flask.Request.cookies>`_.
        if 'ipuser' in session:
            sid = session['ipuser']
        else:
            # See `request.remove_addr <http://werkzeug.pocoo.org/docs/0.12/wrappers/#werkzeug.wrappers.BaseRequest.remote_addr>`_.
            sid = str(uuid.uuid1().int)+"@"+request.remote_addr

    # We set our own session anyway to eliminate many of the extraneous anonymous
    # log entries that come from auth timing out even but the user hasn't reloaded
    # the page.
    session['ipuser'] = sid

    # Get the request arguments.
    act = request.args.get('act')
    div_id = request.args.get('div_id')
    event = request.args.get('event')
    course = request.args.get('course')
    tt = request.args.get('time', 0)
    ts = datetime.now()

    try:
        db.session.add(UseInfo(sid=sid, act=act[0:512], div_id=div_id, event=event, timestamp=ts, course_id=course))
        db.session.commit()
    except:
        current_app.logger.debug('failed to insert log record for {} in {} : {} {} {}'.format(sid, course, div_id, event, act))

    # See `jsonify <http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify>`_. TODO: Return False if there's no session?
    return jsonify(log=True, is_authenticated=is_authenticated())
