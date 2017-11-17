# ***************************************************************
# |docname| - Unit tests for `../runestone/book_server/server.py`
# ***************************************************************
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

# Third-party imports
# -------------------
# None.

# Local imports
# -------------
# The ``app`` import is required for the fixtures to work.
from base_test import BaseTest, app, LoginContext, url_joiner
from runestone.book_server.server import book_server
from runestone.api.endpoints import api
from runestone.model import db, Courses, UseInfo

# Testing
# =======
#
# Utilities
# ---------
# The common path prefix for testing the server: sp (for server path).
def sp(_str='', **kwargs):
    return url_joiner(book_server.url_prefix, _str, **kwargs)
# Same for the book API: ap (api path)
def ap(_str='', **kwargs):
    return url_joiner(api.url_prefix, _str, **kwargs)

# Server tests
# ------------
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
# ---------
class TestRunestoneApi(BaseTest):
    # An example of checking the JSON returned from a URL.
    def test_1(self):
        with self.login_context:
            self.get_valid_json(ap('hsblog', act=1, div_id=2, event=3, course=4, time=5), dict(
                log=True,
                is_authenticated=True,
            ))
            # Check selected columns of the database record. (Omit the id and timestamp).
            u = UseInfo['brad@test.user']._query.add_columns(UseInfo.sid, UseInfo.act, UseInfo.div_id, UseInfo.event, UseInfo.course_id).all()
            # The result of the query is a KeyedTyple. Use `_asdict <http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.util.KeyedTuple._asdict>`_ to convert it to a dict for easy comparison.
            assert [_._asdict() for _ in u] == [dict(
                sid='brad@test.user',
                act='1',
                div_id='2',
                event='3',
                course_id='4',
            )]

# Web2PyBoolean tests
# -------------------
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
