#!/usr/bin/env python3

import sys
import os

import unittest
import tempfile

sys.path.insert(0, 'server')
import watchserver
import stations

sys.path.insert(0, 'client')
import stationreport


# Try to control ordering of tests.
# Everybody says they're run alphabetically, but they're not.
# unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: cmp(y, x)

class ServerTests(unittest.TestCase):

    # executed prior to each test
    def setUp(self):
        os.environ["HOME"] = "/home/NOBODY_HERE"
        self.savedir = "test/files/"
        stations.initialize(savedir_path=self.savedir)

        # self.app = watchserver.app
        watchserver.app.testing = True
        self.app = watchserver.app.test_client()

    # executed after each test
    def tearDown(self):
        for f in os.listdir(self.savedir):
            if f.startswith("UnitTest"):
                os.unlink(os.path.join(self.savedir, f))

    def test_main_page(self):
        rv = self.app.get('/', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        assert b'<h1 class="title">Watch Weather: Menu</h1>' in rv.data

    def test_without_config(self):
        rv = self.app.get('/', follow_redirects=True)

    # Make a report from a dummy client, and make sure it's remembered.
    def test_client_report(self):
        stationreport.initialize("testclient")
        stationreport.stationreport('localhost', "UnitTest",
                                    test_client=self.app)

        # Now see if it showed up on the server
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        assert b'<a href="/details/UnitTest">Details</a>' in rv.data

        # Make sure it's on the summary page
        rv = self.app.get('/stations')
        self.assertEqual(rv.status_code, 200)
        assert b'<legend>UnitTest' in rv.data

        # Make sure there's a details page for it
        rv = self.app.get('/details/UnitTest')
        self.assertEqual(rv.status_code, 200)
        assert b'<h1 class="title">UnitTest Details</h1>' in rv.data
        assert b'<td>Temperature\n<td class="val">85.0<tr>' in rv.data


if __name__ == '__main__':
    unittest.main()

