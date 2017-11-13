:orphan:

A New and Improved Runestone Server
===================================

Goals
-----
* Move away from web2py
* Reduce duplication and hassle by serving one copy of each book dynamically

Overview
--------
This app makes use of `Flask Blueprints <http://flask.pocoo.org/docs/0.12/blueprints/>`_.  Its a nice way to modularize your application, but it makes understanding the app a little more difficult at first.

Installation
------------
#.  ``pip install -U -r requirements.txt``
#.  Download web2py. Copy the ``gluons`` directory to the package root, so it can be imported.

Running
-------
#.  Set the ``DEV_DBURL`` to a valid DB URL. (See `config.py`).
#.  Run ``python wsgi.py``
#.  Browse to http://127.0.0.1:8080/runestone.

Testing
-------
Run ``python -m pytest test`` from the root project directory.

Building docs
-------------
Execute ``sphinx-build -d _build\doctrees . _build\html`` in the root project directory.

