***********************
``test/`` -- Unit tests
***********************
The overall structure: `conftest.py` is `automatically imported <https://docs.pytest.org/en/latest/plugins.html>`_. It sets up a clean database populated with test data for each test. The fixtures defined there are used by `base_test.py` to define a base class and utilities. Finally, `test_all.py` uses this base class to define the actual tests.

.. toctree::
    :glob:

    *.py
