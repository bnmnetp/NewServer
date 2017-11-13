# ************************************
# |docname| - Initialize Flask plugins
# ************************************

import inspect as py_inspect
from sqlalchemy import orm
from flask_sqlalchemy import SQLAlchemy, SignallingSession
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask import _app_ctx_stack
from pythonic_sqlalchemy_query import QueryMakerSession, _is_mapped_class, QueryMaker

# Flask-SQLAlchemy customization
# ==============================
# Create a SQLAlchemy class that includes the pythonic_sqlalchemy_query extension.
#
# First, create a Session composed of `Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org/2.3/api/#flask_sqlalchemy.SignallingSession>`_ and `pythonic_sqlalchemy_query <http://pythonic-sqlalchemy-query.readthedocs.io/en/latest/pythonic_sqlalchemy_query.py.html#querymakersession>`_'s additions.
class SignallingSessionPythonicQuery(SignallingSession, QueryMakerSession):
    pass

# By default, SQLAlchemy doesn't proxy getattr in a scoped session. Add this.
class PythonicQueryScopedSession(orm.scoped_session):
    def __getattr__(self, name):
        # TODO: Shady. I don't see any other way to accomplish this, though.
        #
        # Get the caller's `frame record <https://docs.python.org/3/library/inspect.html#the-interpreter-stack>`_.
        callers_frame_record = py_inspect.stack()[1]
        # From this, get the `frame object <https://docs.python.org/3/library/inspect.html#types-and-members>`_ (index 0), then the global namespace seen by that frame.
        g = callers_frame_record[0].f_globals
        if (name in g) and _is_mapped_class(g[name]):
            return QueryMaker(query=self.registry().query().select_from(g[name]))
        else:
            return super().__getattr__(name)

# Then, use these in the `Flask-SQLAlchemy session <http://flask-sqlalchemy.pocoo.org/2.3/api/#sessions>`_.
class SQLAlchemyPythonicQuery(SQLAlchemy):
    # The only change from the Flask-SQLAlchemy v2.3.2 source: ``PythonicQueryScopedSession`` instead of ``orm.scoped_session``.
    def create_scoped_session(self, options=None):
        if options is None:
            options = {}

        scopefunc = options.pop('scopefunc', _app_ctx_stack.__ident_func__)
        options.setdefault('query_cls', self.Query)
        return PythonicQueryScopedSession(
            self.create_session(options), scopefunc=scopefunc
        )
    def create_session(self, options):
        # The only change from the Flask-SQLAlchemy v2.3.2 source: SignallingSessionPythonicQuery instead of SignallingSession.
        return orm.sessionmaker(class_=SignallingSessionPythonicQuery, db=self, **options)

# Create extensions
# =================
bootstrap = Bootstrap()
db = SQLAlchemyPythonicQuery()
mail = Mail()
