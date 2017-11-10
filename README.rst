A New and Improved Runestone Server
===================================

Goals
-----
* Move away from web2py
* Reduce duplication and hassle by serving one copy of each book dynamically

Overview
--------
This app makes use of `Flask Blueprints <http://flask.pocoo.org/docs/0.12/blueprints/>`_.  Its a nice way to modularize your application, but it makes understanding the app a little more difficult at first.

Structure:

-   wsgi.py  -- simple driver file for kicking off the app
-   runestone/ -- The root of a python package (eventually distributed to pypi)

    -   __init__.py
    -   model.py
    -   book_server/

        -   __init__.py
        -   server.py
    -   api

        -   __init__.py
        -   endpoints.py

Testing
-------
#.  Set the ``DEV_DBURL`` to a valid DB URL. (See ``runestone/config.py``).
#.  Run ``python wsgi.py``
#.  Browse to http://127.0.0.1:8080/runestone.
