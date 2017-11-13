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
# None.

# Third-party imports
# -------------------
# None.

# Local imports
# -------------
from base_test import app, BaseTest, LoginContext

# Tests
# -----
class TestRunestoneServer(BaseTest):
    # Check the root path view.
    def test_1(self):
        with LoginContext(self, 'brad@test.user', 'grouplens'):
            self.get_valid('/runestone', follow_redirects=True)

    # Make sure the 404 page works.
    def test_2(self):
        self.get_invalid('xxx.html')

    # An example of checking the JSON returned from a URL.
    questions_url = '/book/unsigned_8-_and_16-bit_ops/introduction.s.html/questions'
    def example_test_9(self):
        with LoginContext(self, 'student'):
            self.get_valid_json(self.questions_url,
                           {'define_label': ['foo:', 2, 2, 'correct'],
                            'comment': ['10000', 0, 1, 'Incorrect.']})
