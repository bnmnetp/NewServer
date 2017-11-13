# ************************************
# |docname| - Initialize Flask plugins
# ************************************

import inspect as py_inspect
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy, SignallingSession
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask import _app_ctx_stack
from flask_sqlalchemy.model import Model, DefaultMeta
from pythonic_sqlalchemy_query import QueryMakerSession, _is_mapped_class, QueryMaker

# Flask-SQLAlchemy customization
# ==============================
# Create a SQLAlchemy class that includes the pythonic_sqlalchemy_query extension.
#
# Enable syntax such as ``Model[id]`` for queries.
class QueryMakerFlaskDeclarativeMeta(DefaultMeta):
    def __getitem__(cls, key):
        # Extract the session from the Flask-SQLAlchemy `query <http://flask-sqlalchemy.pocoo.org/2.3/queries/#querying-records>`_ attribute.
        session = cls.query.session
        # Build a new query from here, since ``cls.query`` has already invoked ``add_entity`` on ``cls``.
        return QueryMaker(query=session.query().select_from(cls))[key]

# Create a Session composed of `Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org/2.3/api/#flask_sqlalchemy.SignallingSession>`_ and `pythonic_sqlalchemy_query <http://pythonic-sqlalchemy-query.readthedocs.io/en/latest/pythonic_sqlalchemy_query.py.html#querymakersession>`_'s additions.
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
    def __init__(self, *args, **kwargs):
        # Provide a declarative_base model for Flask-SQLAlchemy. This is almost identical to code in  ``flask_sqlalchemy.SQLAlchemy.make_declarartive_base``, but using our custom metaclass.
        metadata = kwargs.pop('metadata', None)
        assert 'model_class' not in kwargs
        kwargs['model_class'] = declarative_base(
            cls=Model,
            name='Model',
            metadata=metadata,
            # Use our custom metaclass.
            metaclass=QueryMakerFlaskDeclarativeMeta
        )

        super().__init__(*args, **kwargs)

    # The only change from the Flask-SQLAlchemy v2.3.2 source: ``PythonicQueryScopedSession`` instead of ``orm.scoped_session``.
    def create_scoped_session(self, options=None):
        if options is None:
            options = {}

        scopefunc = options.pop('scopefunc', _app_ctx_stack.__ident_func__)
        options.setdefault('query_cls', self.Query)
        return PythonicQueryScopedSession(
            self.create_session(options), scopefunc=scopefunc
        )

    # The only change from the Flask-SQLAlchemy v2.3.2 source: SignallingSessionPythonicQuery instead of SignallingSession.
    def create_session(self, options):
        return orm.sessionmaker(class_=SignallingSessionPythonicQuery, db=self, **options)

# Create extensions
# =================
bootstrap = Bootstrap()
db = SQLAlchemyPythonicQuery()
mail = Mail()
