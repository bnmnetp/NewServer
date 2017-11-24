# ************************************************
# |docname| - provide Ajax endpoints used by books
# ************************************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
import uuid
from datetime import datetime

# Third-party imports
# -------------------
from flask import Blueprint, request, session, jsonify, current_app
from flask_user import current_user, is_authenticated

# Local imports
# -------------
from ..model import db, Useinfo, TimedExam, MchoiceAnswers, Courses, Questions

# Blueprint
# =========
# Define the API's blueprint.
api = Blueprint('api', __name__, url_prefix='/api')


# Return the length of a SQLAlchemy column.
def sql_len(col):
    # Taken from https://stackoverflow.com/a/1778993.
    return col.property.columns[0].type.length


# .. _hsblog endpoint:
#
# hsblog endpoint
# ===============
# Log data to Useinfo and to the appropriate table. TODO: Arguments:
#
# act
#   The action associated with this event. TODO: what exactly is this?
#
# div_id
#   The ID of the div containing this problem.
#
# course
#   The course containing this problem, which must mach an entry in Courses.course_name.
#
# event
#   The type of event being logged. Valid values are:
#
#   timedExam
#       A timed exam event. The following additional arguments for this event are:
#
#       act
#           Must be 'finish' or 'reset'.
#
#       tt
#           The time taken to finish this exam.
#
#       correct
#           The number of correct answers.
#
#       incorrect
#           The number of incorrect answers.
#
#       skipped
#           The number of skipped problems.
#
#   mChoice
#       A multiple-choice answer. Additional arguments:
#
#       answer
#           The answer for the question, as a string. TODO: format?
#
#       correct
#           True if this answer is correct.
#
# TODO: Check these changes from existing code:
#
# - Old code didn't do anything if event='timedExam' but act isn't 'reset' or 'finish'. New code returns Log=False in this case.
# - Old code allows non-authenticated ``timedExam`` inserts to TimedExam. New code does not.
# - New code returns is_authenticated, prompting client-side JavaScript to ask for a login and signaling that the data provided **was not** saved in the event-specific table! It also validates parameters and returns an error if they're not valid.
@api.route('/hsblog')
def log_book_event():
    is_auth = is_authenticated()
    if is_auth:
        # ``current_user`` is a `proxy <https://flask-login.readthedocs.io/en/latest/#flask_login.current_user>`_ for the currently logged-in user. It returns ``None`` if no user is logged in.
        sid = current_user.username
        # If the user wasn't logged in, but is now, update all ``hsblog`` entries to their username.
        session_sid = session.get('sid')
        if session_sid != sid:
            # Yes, so update all ``session_sid`` entries.
            for _ in Useinfo[session_sid]:
                _.sid = sid
    else:
        # Create a uuid for a user that's not logged in. See `request.cookies <http://flask.pocoo.org/docs/0.12/api/#flask.Request.cookies>`_.
        if 'sid' in session:
            sid = session['sid']
        else:
            # See `request.remove_addr <http://werkzeug.pocoo.org/docs/0.12/wrappers/#werkzeug.wrappers.BaseRequest.remote_addr>`_.
            sid = str(uuid.uuid1().int) + "@" + request.remote_addr

    # We set our own session anyway to eliminate many of the extraneous anonymous
    # log entries that come from auth timing out even but the user hasn't reloaded
    # the page.
    session['sid'] = sid

    # Get the request arguments.
    act = request.args.get('act', '')
    div_id = request.args.get('div_id', '')
    event = request.args.get('event', '')
    course = request.args.get('course', '')

    ts = datetime.now()

    # Validate them. The event is validated inside ``if is_auth``.
    return_kwargs = dict(log=False, is_authenticated=is_auth)
    if Courses[course].q.count() == 0:
        return jsonify(error='Unknown course {}.'.format(course), **return_kwargs)
    if Questions[div_id].q.count() == 0:
        return jsonify(error='Unknown div_id {}.'.format(div_id), **return_kwargs)
    # Check string sizes for parameters not validated yet.
    if len(event) > sql_len(Useinfo.act):
        return jsonify(error='Event length {} too large.'.format(len(event)), **return_kwargs)
    if len(act) > sql_len(Useinfo.act):
        return jsonify(error='Act length {} too large.'.format(len(act)), **return_kwargs)

    try:
        db.session.add(Useinfo(sid=sid, act=act, div_id=div_id, event=event, timestamp=ts, course_id=course))
        db.session.commit()
        log = True
    except:
        current_app.logger.debug('failed to insert log record for {} in {} : {} {} {}'.format(sid, course, div_id, event, act))
        log = False

    if is_auth:
        answer = request.args.get('answer')
        correct = request.args.get('correct')
        if event == 'timedExam':
            if act not in ('finish', 'reset'):
                # Return log=False on an invalid ``act``.
                return jsonify(log=False, is_authenticated=is_auth)

            # Gather args. Provide a default of 0, since no default produces None, which leads to an exception from executing ``int(None)``
            correct = int(request.args.get('correct', 0))
            incorrect = int(request.args.get('incorrect', 0))
            skipped = int(request.args.get('skipped', 0))
            time_taken = int(request.args.get('time', 0))

            try:
                db.session.add(TimedExam(
                    sid=sid,
                    course_name=course,
                    correct=correct,
                    incorrect=incorrect,
                    skipped=skipped,
                    time_taken=time_taken,
                    timestamp=ts,
                    div_id=div_id,
                    reset=act == 'reset' or None,
                ))
            except Exception as e:
                current_app.logger.debug('failed to insert a timed exam record for {} in {} : {}'.format(sid, course, div_id))
                current_app.logger.debug('correct {} incorrect {} skipped {} time {}'.format(correct, incorrect, skipped, time_taken))
                current_app.logger.debug('Error: {}'.format(e.message))

        elif event == 'mChoice':
            # Has the user already submitted a correct answer for this question?
            if MchoiceAnswers[sid, div_id, course][True].q.count() == 0:
                # No, so insert this answer.
                db.session.add(MchoiceAnswers(
                    sid=sid,
                    timestamp=ts,
                    div_id=div_id,
                    answer=answer,
                    correct=correct,
                    course_name=course
                ))

        else:
            return jsonify(log=False, is_authenticated=is_auth, error='Unknown event {}.'.format(event))

        db.session.commit()

    # See `jsonify <http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify>`_.
    return jsonify(log=log, is_authenticated=is_auth)
