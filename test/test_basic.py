#!/usr/bin/env python3

import sys
import os

import unittest
import tempfile

sys.path.insert(0, 'server')
import watchserver

# For tests that use clients:
sys.path.insert(0, 'client')

# Try to control ordering of tests.
# Everybody says they're run alphabetically, but they're not.
# unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: cmp(y, x)

class BasicTests(unittest.TestCase):

    # executed prior to each test
    def setUp(self):
        os.environ["HOME"] = "/home/NOBODY_HERE"
        self.app = watchserver.app
        watchserver.app.testing = True
        self.app = watchserver.app.test_client()

    # executed after each test
    def tearDown(self):
        pass

    def test_ZZZ_main_page(self):
        rv = self.app.get('/', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        assert b'Watchweather Server home page' in rv.data

    def test_without_config(self):
        rv = self.app.get('/', follow_redirects=True)

    def test_testclient(self):
        import stationreport

        stationreport.initialize("testclient")
        stationreport.stationreport('localhost', "Unit test",
                                    test_client=self.app)

        # Now see if it showed up on the server
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        assert b'<a href="/details/Unit test">Unit test Details</a>' in rv.data

        # Make sure it's on the summary page
        rv = self.app.get('/stations')
        self.assertEqual(rv.status_code, 200)
        assert b'<legend>Unit test' in rv.data

        # Make sure there's a details page for it
        rv = self.app.get('/details/Unit test')
        self.assertEqual(rv.status_code, 200)
        assert b'<h1>Unit test</h1>' in rv.data
        assert b'<td>Temperature\n<td class="val">85.0<tr>' in rv.data

if __name__ == '__main__':
    unittest.main()

