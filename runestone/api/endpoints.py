from flask import Blueprint, request, make_response
from ..model import LogInfo
import uuid
import datetime
import json


api = Blueprint('api', __name__, url_prefix='/api')
from runestone import db,app

@api.route('/hsblog')
def log_book_event():
    setCookie = False
    sid = request.cookies.get('ipuser')  # quickest way to get the sid

    # if auth.user:    # todo: How can we make web2py and flask share login information? - we can get the session cookie but we need to unscramblepython
    #     sid = auth.user.username
    #     compareAndUpdateCookieData(sid)
    #     setCookie = True    # we set our own cookie anyway to eliminate many of the extraneous anonymous
    #                         # log entries that come from auth timing out even but the user hasn't reloaded
    #                         # the page.
    # else:
    #     if request.cookies.has_key('ipuser'):
    #         sid = request.cookies['ipuser'].value
    #         setCookie = True
    #     else:
    #         sid = str(uuid.uuid1().int)+"@"+request.client
    #         setCookie = True
    act = request.args.act
    div_id = request.args.div_id
    event = request.args.event
    course = request.args.course
    ts = datetime.datetime.now()
    tt = request.args.time
    if not tt:
        tt = 0

    try:
        li = LogInfo(sid=sid, act=act, div_id=div_id, event=event, timestamp=ts, course_id=course)
        db.add(li)
        db.commit()
    except:
        app.logger.debug('failed to insert log record for {} in {} : {} {} {}'.format(sid, course, div_id, event, act))

    response = make_response()
    response.headers['content-type'] = 'application/json'
    res = {'log':True}
    if setCookie:
        response.cookies['ipuser'] = sid
        response.cookies['ipuser']['expires'] = 24*3600*90
        response.cookies['ipuser']['path'] = '/'
    return json.dumps(res)

