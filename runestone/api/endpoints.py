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
from functools import wraps

# Third-party imports
# -------------------
from flask import Blueprint, request, session, jsonify
from flask_user import current_user, is_authenticated

# Local imports
# -------------
from ..model import db, Useinfo, TimedExam, MchoiceAnswers, Courses, Questions, Web2PyBoolean

# Blueprint
# =========
# Define the API's blueprint.
api = Blueprint('api', __name__, url_prefix='/api')


# Validators
# ==========
# A common task is validation of request arguments. These functions provide simple validation, and expect an endpoint to be wrapped in a try/except RequestValidationFailure block which returns the appropriate error. While there are other libraries (`webargs <https://webargs.readthedocs.io>`_ looks nice), this seems to balance simplicity and functionality.
#
# Validate a request argument. It returns a string, containing the validated argument, or raises a ``RequestValidationFailure``.
def generic_validator(
    # _`arg_name:` The name of the request argument, as a string.
    arg_name,
    # Either: A function which takes one parameter, the argument's value. It must return a falsey value if the value did not validate. Or: None (no validation).
    validation_func,
    # Either a function which takes one paraemter, the argument's value, and returns a string use to report the error; or a string: ``exception_func.format(arg_name, arg)`` should report the error.
    exception_func,
    # _`default`: A default value for this argument if none was given.
    default=None):

    arg = request.args.get(arg_name, default)
    if arg is None:
        raise RequestValidationFailure('Missing argument {}.'.format(arg_name))
    if validation_func and not validation_func(arg):
        if isinstance(exception_func, str):
            raise RequestValidationFailure(exception_func.format(arg_name, arg))
        else:
            raise RequestValidationFailure(exception_func(arg))
    return arg


# Validate a request argument based on a SQLAlchemy column. The value (appropriate converted) is returned.
def sql_validator(
    # See arg_name_.
    arg_name,
    # An SQLAlchemy column used to define the validation and type of returned value.
    column,
    # See default_.
    default=None):

    # Based on https://stackoverflow.com/a/1778993.
    sql_type = column.property.columns[0].type
    if isinstance(sql_type, db.String):
        return generic_validator(
            arg_name,
            lambda arg: len(arg) <= sql_type.length,
            lambda arg: 'Argument {} length {} exceeds the maximum length of {}.'.format(arg_name, len(arg), sql_type.length),
            default
        )
    elif isinstance(sql_type, Web2PyBoolean):
        bool_string = generic_validator(
            arg_name,
            lambda arg: arg in ('true', 'T', 'false', 'F', ''),
            'Argument {} supplied an invalid boolean value of {}.',
            default
        )
        if bool_string == '':
            return None
        else:
            return bool_string in ('true', 'T')
    elif isinstance(sql_type, db.Integer):
        str_val = generic_validator(arg_name, None, '')
        try:
            return int(str_val)
        except ValueError:
            raise RequestValidationFailure('Unable to convert argument {} to an integer.'.format(arg_name))
    else:
        # We don't know how to validate this type.
        assert False


# An Exception to indicate request validation failed.
class RequestValidationFailure(Exception):
    pass


# A decorator to make request validation handling a bit prettier. Provide it with a function to call if request validation fails. This function should take one parameter, the RequestValidationFailure instance raised.
def request_validation_handler(on_error_func):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except RequestValidationFailure as e:
                return on_error_func(e)
        return wrapper
    return decorator


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
# - Old code has try/except blocks with logging. New code does not. Hopefully, better testing has fixed these failures.
# - New code returns is_authenticated, prompting client-side JavaScript to ask for a login and signaling that the data provided **was not** saved in the event-specific table! It also validates parameters and returns an error if they're not valid.
@api.route('/hsblog')
@request_validation_handler( lambda e: jsonify(error=e.args[0], log=False, is_authenticated=is_authenticated()) )
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
    ts = datetime.now()

    # Get and validate the request args. The event is validated inside ``if is_auth``.
    course = generic_validator('course', lambda arg: Courses[arg].q.count(), 'Unknown course {1}.')
    div_id = generic_validator('div_id', lambda arg: Questions[arg].q.count(), 'Unknown div_id {1}.')
    # Check string sizes for parameters not validated yet.
    event = sql_validator('event', Useinfo.act)
    act = sql_validator('act', Useinfo.act)

    db.session.add(Useinfo(sid=sid, act=act, div_id=div_id, event=event, timestamp=ts, course_id=course))
    db.session.commit()

    if is_auth:

        if event == 'timedExam':
            if act not in ('finish', 'reset'):
                # Return log=False on an invalid ``act``.
                return jsonify(log=False, is_authenticated=is_auth)

            db.session.add(TimedExam(
                sid=sid,
                course_name=course,
                correct=sql_validator('correct', TimedExam.correct),
                incorrect=sql_validator('incorrect', TimedExam.incorrect),
                skipped=sql_validator('skipped', TimedExam.skipped),
                time_taken=sql_validator('time', TimedExam.time_taken),
                timestamp=ts,
                div_id=div_id,
                reset=act == 'reset' or None,
            ))

        elif event == 'mChoice':
            # Has the user already submitted a correct answer for this question?
            if MchoiceAnswers[sid, div_id, course][True].q.count() == 0:
                # No, so insert this answer.
                db.session.add(MchoiceAnswers(
                    sid=sid,
                    timestamp=ts,
                    div_id=div_id,
                    answer=sql_validator('answer', MchoiceAnswers.answer),
                    correct=sql_validator('correct', MchoiceAnswers.correct),
                    course_name=course
                ))

        else:
            return jsonify(log=False, is_authenticated=is_auth, error='Unknown event {}.'.format(event))

        db.session.commit()

    # See `jsonify <http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify>`_.
    return jsonify(log=True, is_authenticated=is_auth)
