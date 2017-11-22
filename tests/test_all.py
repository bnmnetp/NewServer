# **********************
# |docname| - Unit tests
# **********************
# .. contents::
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
from unittest.mock import patch
from contextlib import contextmanager
from datetime import datetime, timedelta

# Third-party imports
# -------------------
# None.

# Local imports
# -------------
# The ``app`` import is required for the fixtures to work.
from base_test import BaseTest, app, LoginContext, url_joiner, result_remove
from runestone.book_server.server import book_server
from runestone.api.endpoints import api
from runestone.model import db, Courses, Useinfo, TimedExam


# Utilities
# =========
# The common path prefix for testing the server: sp (for server path).
def sp(_str='', **kwargs):
    return url_joiner(book_server.url_prefix, _str, **kwargs)
# Same for the book API: ap (api path)
def ap(_str='', **kwargs):
    return url_joiner(api.url_prefix, _str, **kwargs)


# Server tests
# ============
class TestRunestoneServer(BaseTest):
    # Check the root path view. This is fairly pointless, since this is a temporary page anyway.
    def test_1(self):
        self.must_login(sp())
        with self.login_context:
            self.get_valid(sp(), b'Hello World!', follow_redirects=True)

    # Make sure the 404 page works.
    def test_2(self):
        self.get_invalid('xxx.html')

    # Check that accessing a book via a child course works.
    def test_3(self):
        # Make sure this requires a login.
        url = sp('test_child_course1/foo.html')
        self.must_login(url)

        mock_render_patch = patch('runestone.book_server.server.render_template', return_value='')
        with self.login_context:
            with mock_render_patch as mock_render:
                # When logged in, everything works.
                self.get_valid(url)
            # When not logged in, a login should be requested.
            self.must_login(url)
            mock_render.assert_called_once_with('test_base_course/foo.html', basecourse='test_base_course', login_required='true', python3='true')

        # Check that flags are passed (login_required and python3 are different). Check that no login is needed.
        with mock_render_patch as mock_render:
            self.get_valid(sp('test_child_course2/foo.html'))
            mock_render.assert_called_once_with('test_base_course/foo.html', basecourse='test_base_course', login_required='false', python3='false')

    # Check that static assets are passed through.
    def test_4(self):
        with self.login_context:
            with patch('runestone.book_server.server.send_from_directory', return_value='') as mock_send_from_directory:
                self.get_valid(sp('test_child_course1/_static/foo.css'))
                # Check only the second arg. Note that ``call_args`` `returns <https://docs.python.org/3/library/unittest.mock.html#calls-as-tuples>`_ ``(args, kwargs)``.
                assert mock_send_from_directory.call_args[0][1] == 'test_base_course/_static/foo.css'

                self.get_valid(sp('test_child_course1/_images/foo.png'))
                assert mock_send_from_directory.call_args[0][1] == 'test_base_course/_images/foo.png'


# API tests
# =========
class TestRunestoneApi(BaseTest):
# hsblog
# ------
    hsblog = 'hsblog'

    # Check the consistency of values put in Useinfo.
    def test_1(self):
        with self.login_context:
            self.get_valid_json(ap(
                self.hsblog,
                act=1,
                div_id='test_div_id',
                event='mChoice',
                course='test_child_course1',
                time=5
            ), dict(
                log=True,
                is_authenticated=True,
            ))
            # Check the timestamp.
            assert (Useinfo[self.username].timestamp.q.scalar() - datetime.now()) < timedelta(seconds=2)
            # Check selected columns of the database record. (Omit the id and timestamp).
            results = result_remove(Useinfo.query, 'id', 'timestamp')
            assert results == [dict(
                sid=self.username,
                act='1',
                div_id='test_div_id',
                event='mChoice',
                course_id='test_child_course1',
            )]

    # Check that unauthenticed access produces a consistent sid.
    def test_2(self):
        def go(is_auth=False):
            self.get_valid_json(ap(
                self.hsblog,
                act='xxx',
                course='test_child_course1',
                div_id='test_div_id',
                event='mChoice',
            ), dict(
                log=True,
                is_authenticated=is_auth,
            ))
        go()
        go()
        r = db.session.Useinfo.sid.q.all()
        assert len(r) == 2
        assert r[0] == r[1]

        # If this user logs in, then make sure the sid is updated. There should now to be 3 log entries, all with sid=username.
        with self.login_context:
            go(True)
        assert Useinfo[self.username].q.count() == 3

    # Check that invalid parameters return an error.
    def test_2_1(self):
        # Undefined course.
        self.get_valid_json(ap(
            self.hsblog,
            act='xxx',
        ), dict(
            log=False,
            is_authenticated=False,
            error='Unknown course .',
        ))

        # Undefined event.
        with self.login_context:
            self.get_valid_json(ap(
                self.hsblog,
                div_id='test_div_id',
                act='xxx',
                course='test_child_course1',
            ), dict(
                log=False,
                is_authenticated=True,
                error='Unknown event .',
            ))

            self.get_valid_json(ap(
                self.hsblog,
                act='xxx',
                course='test_child_course1',
            ), dict(
                log=False,
                is_authenticated=True,
                error='Unknown div_id .',
            ))

        # Strings that are too long for a column.
        self.get_valid_json(ap(
            self.hsblog,
            event='x'*600,
            course='test_child_course1',
            div_id='test_div_id',
        ), dict(
            log=False,
            is_authenticated=False,
            error='Event length 600 too large.',
        ))
        self.get_valid_json(ap(
            self.hsblog,
            event='xxx',
            act='x'*600,
            course='test_child_course1',
            div_id='test_div_id',
        ), dict(
            log=False,
            is_authenticated=False,
            error='Act length 600 too large.',
        ))

    # Check timed exam entries.
    def test_3(self):
        def go(act, log, auth=True):
            self.get_valid_json(
                ap(
                    self.hsblog,
                    div_id='test_div_id',
                    act=act,
                    event='timedExam',
                    course='test_child_course1',
                    correct=1,
                    incorrect=2,
                    skipped=3,
                    time=4,
                ), dict(
                    log=log,
                    is_authenticated=auth,
                )
            )
        # No entry - not logged in.
        go('reset', True, False)
        with self.login_context:
            # Invalid act.
            go('xxx', False)
            # Valid flavors
            go('reset', True)
            go('finish', True)

        # Check the timestamp.
        assert (TimedExam[self.username].timestamp.q.first()[0] - datetime.now()) < timedelta(seconds=2)

        # Check the results.
        results = result_remove(TimedExam.query, 'id', 'timestamp')
        common_items = dict(
            sid=self.username,
            course_name='test_child_course1',
            correct=1,
            incorrect=2,
            skipped=3,
            time_taken=4,
            div_id='test_div_id',
        )
        assert results == [
            dict(
                reset=True,
                **common_items
            ), dict(
                reset=None,
                **common_items,
            )
        ]


# Web2PyBoolean tests
# ===================
class TestWeb2PyBoolean(BaseTest):
    @contextmanager
    def manual_write_bool(self, bool_):
        # Change a True/False to 'T' or 'F'. Leave None as is.
        if bool_ is True:
            bool_ = 'T'
        elif bool_ is False:
            bool_ = 'F'
        else:
            assert bool_ is None

        db.engine.execute(db.text("insert into courses (course_name, python3) values ('bool_test', :bool_)"), bool_=bool_)
        yield
        db.engine.execute(db.text("delete from courses where course_name='bool_test';"))

    @contextmanager
    def orm_write_bool(self, bool_):
        db.session.add(Courses(course_name='bool_test', python3=bool_))
        db.session.commit()
        yield
        for _ in Courses['bool_test']:
            db.session.delete(_)
        db.session.commit()

    def manual_read_bool(self):
        result = db.engine.execute(db.text("select python3 from courses where course_name='bool_test'")).fetchall()
        assert len(result) == 1
        assert len(result[0].items()) == 1
        return result[0][0]

    def orm_read_bool(self):
        return Courses['bool_test'].python3.q.scalar()

    # Test that web2py boolean values are read back correctly from the database.
    def test_1(self):
        # Manually write values to the database, then read them back.
        with self.manual_write_bool(True):
            assert self.orm_read_bool() is True
        with self.manual_write_bool(False):
            assert self.orm_read_bool() is False
        with self.manual_write_bool(None):
            assert self.orm_read_bool() is None

    # Test that web2py boolean values are written correctly to the database.
    def test_2(self):
        # Write a value, then manually query the result.
        with self.orm_write_bool(True):
            assert self.manual_read_bool() == 'T'
        with self.orm_write_bool(False):
            assert self.manual_read_bool() == 'F'
        with self.orm_write_bool(None):
            assert self.manual_read_bool() is None
