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

    def test_main_page(self):
        rv = self.app.get('/', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        assert b'<h1>Watch Weather</h1>' in rv.data

    def test_without_config(self):
        rv = self.app.get('/', follow_redirects=True)

    '''
    # test_client_report doesn't work because stationreport.post_report()
    # uses requests.get -- it doesn't have the flask app object.
    # To test this, need to either run an actual server on localhost,
    # or write a mock post_report() method.
    # I'm not sure if this ever worked, or, if it did, what changed.
    def test_client_report(self):
        import stationreport

        stationreport.initialize("testclient")
        stationreport.stationreport('localhost', "UnitTest",
                                    test_client=self.app)

        # Now see if it showed up on the server
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        print("data:", rv.data)
        assert b'<a href="/details/UnitTest">UnitTest Details</a>' in rv.data

        # Make sure it's on the summary page
        rv = self.app.get('/stations')
        self.assertEqual(rv.status_code, 200)
        assert b'<legend>UnitTest' in rv.data

        # Make sure there's a details page for it
        rv = self.app.get('/details/UnitTest')
        self.assertEqual(rv.status_code, 200)
        assert b'<h1>UnitTest</h1>' in rv.data
        assert b'<td>Temperature\n<td class="val">85.0<tr>' in rv.data
    '''

if __name__ == '__main__':
    unittest.main()

