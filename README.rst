A New and Improved Runestone Server
===================================

Goals
-----

* Move away from web2py
* Reduce duplication and hassle by serving one copy of each book dynamically


Overview
--------

This app makes use of Flask Blueprints.  Its a nice way to modularize your application, but it makes understanding the app a little more difficult at first.

::

    wsgi.py  -- simple driver file for kicking off the app
    runestone/ -- The root of a python package (eventually distributed to pypi)
        __init__.py
        model.py
        book_server/
            __init__.py
            server.py
        api
            __init__.py
            endpoints.py


