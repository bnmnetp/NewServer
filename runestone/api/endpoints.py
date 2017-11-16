# ************************************************
# |docname| - provide Ajax endpoints used by books
# ************************************************
import uuid
import datetime
from flask import Blueprint, request, session, jsonify, current_app
from ..model import UseInfo, db
from flask_user import current_user

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/hsblog')
def log_book_event():
    # A `proxy <https://flask-login.readthedocs.io/en/latest/#flask_login.current_user>`_ for the currently logged-in user. It returns ``None`` if no user is logged in.
    if current_user:
        # Does ``current_user`` consist of a User object? Or something else?
        sid = current_user.username
        # compareAndUpdateCookieData(sid) inlined here.
        if ('ipuser' in session) and (session['ipuser'] != sid):
            # See if this user exists.
            q = UseInfo[sid].q
            if q.length():
                # Yes, so update all ``sid`` entries.
                for _ in q:
                    q.sid = sid
            else:
                # No, so create a new entry. TODO: This makes no sense to me. A more complete entry will be added below -- wait until then!
                db.session.add(UseInfo(sid=sid))
                db.session.commit()
    else:
        # See `request.cookies <http://flask.pocoo.org/docs/0.12/api/#flask.Request.cookies>`_.
        if 'ipuser' in request.cookies:
            sid = session['ipuser']
        else:
            # TODO: does `request.remove_addr <http://werkzeug.pocoo.org/docs/0.12/wrappers/#werkzeug.wrappers.BaseRequest.remote_addr>`_ work?
            sid = str(uuid.uuid1().int)+"@"+request.remote_addr

    # We set our own session anyway to eliminate many of the extraneous anonymous
    # log entries that come from auth timing out even but the user hasn't reloaded
    # the page.
    session['ipuser'] = sid

    act = request.args.get('act')
    div_id = request.args.get('div_id')
    event = request.args.get('event')
    course = request.args.get('course')
    ts = datetime.datetime.now()
    tt = request.args.get('time')
    if not tt:
        tt = 0

    try:
        db.add(UseInfo(sid=sid, act=act[0:512], div_id=div_id, event=event, timestamp=ts, course_id=course))
        db.commit()
    except:
        current_app.logger.debug('failed to insert log record for {} in {} : {} {} {}'.format(sid, course, div_id, event, act))

    # See `jsonify <http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify>`_. TODO: Return False if there's no session?
    return jsonify({'log':True})
