#!/usr/bin/env python3

import sys
import os

import unittest
import tempfile

sys.path.insert(0, 'server')
import watchserver


# Try to control ordering of tests.
# Everybody says they're run alphabetically, but they're not.
# unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: cmp(y, x)

class ServerTests(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()

