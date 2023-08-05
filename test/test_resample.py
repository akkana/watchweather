#!/usr/bin/env python3

import unittest

import sys
sys.path.insert(0, 'server')

import stations

from datetime import datetime, date, timedelta


def roundoff_floats(rsdata):
    for key in rsdata:
        for i, val in enumerate(rsdata[key]):
            if type(val) is float:
                rsdata[key][i] = round(val, 4)


class ResampleTest(unittest.TestCase):

    # executed prior to each test
    def setUp(self):
        pass

    # executed after each test
    def tearDown(self):
        pass

    def test_resample(self):
        self.maxDiff = None
        stations.savedir = "test/files/"

        rsdata = stations.read_csv_data_resample("Outdoor", ["temperature"],
                                                 datetime(2022, 6, 26, 9, 0),
                                                 datetime(2022, 6, 26, 10, 0),
                                                 timedelta(minutes=20))
        roundoff_floats(rsdata)
        self.assertEqual(rsdata,
                         {
                             't': [datetime(2022, 6, 26, 9, 0),
                                   datetime(2022, 6, 26, 9, 20),
                                   datetime(2022, 6, 26, 9, 40),
                                   datetime(2022, 6, 26, 10, 0)],
                             'temperature': [52.935, 53.1103, 53.0179, 53.4]
                    })

        # test with both files there
        rsdata = stations.read_csv_data_resample("Outdoor", ["temperature"],
                                                 datetime(2022, 6, 26, 23, 0),
                                                 datetime(2022, 6, 27, 1, 0),
                                                 timedelta(minutes=20))
        roundoff_floats(rsdata)
        self.assertEqual(rsdata,
                         {
                             't': [datetime(2022, 6, 26, 23, 0),
                                   datetime(2022, 6, 26, 23, 20),
                                   datetime(2022, 6, 27, 0, 0),
                                   datetime(2022, 6, 27, 0, 20),
                                   datetime(2022, 6, 27, 0, 40),
                                   datetime(2022, 6, 27, 1, 0)],
                             'temperature': [
                                 53.8, 53.56, 53.45, 53.1317, 53.04, 52.9]
                         })

        # test first file missing
        rsdata = stations.read_csv_data_resample("Outdoor", ["temperature"],
                                                 datetime(2022, 6, 25, 23, 0),
                                                 datetime(2022, 6, 26, 1, 0),
                                                 timedelta(minutes=20))
        roundoff_floats(rsdata)
        self.assertEqual(rsdata,
                         {
                             't': [datetime(2022, 6, 26, 0, 0),
                                   datetime(2022, 6, 26, 0, 20),
                                   datetime(2022, 6, 26, 0, 40),
                                   datetime(2022, 6, 26, 1, 0)],
                             'temperature': [None, 52.92, 53.085, 53.1]
                         })

        # test second file missing
        rsdata = stations.read_csv_data_resample("Outdoor", ["temperature"],
                                                 datetime(2022, 6, 27, 23, 0),
                                                 datetime(2022, 6, 28, 1, 0),
                                                 timedelta(minutes=20))
        roundoff_floats(rsdata)
        self.assertEqual(rsdata,
                         {
                             't': [datetime(2022, 6, 27, 23, 0),
                                   datetime(2022, 6, 27, 23, 20),
                                   datetime(2022, 6, 28, 0, 0)],
                             'temperature': [53.5385, 52.86, 52.55]
                         })

        # test both files missing
        rsdata = stations.read_csv_data_resample("Outdoor", ["temperature"],
                                                 datetime(2021, 6, 10, 23, 0),
                                                 datetime(2021, 6, 11, 1, 0),
                                                 timedelta(minutes=20))
        roundoff_floats(rsdata)
        self.assertEqual(rsdata, {'t': [], 'temperature': []})

        # test two keys
        rsdata = stations.read_csv_data_resample("Outdoor",
                                                 ["temperature",
                                                  "average_wind"],
                                                 datetime(2022, 6, 26, 9, 0),
                                                 datetime(2022, 6, 26, 10, 0),
                                                 timedelta(minutes=20))
        roundoff_floats(rsdata)
        self.assertEqual(rsdata, {
            't': [datetime(2022, 6, 26, 9, 0),
                  datetime(2022, 6, 26, 9, 20),
                  datetime(2022, 6, 26, 9, 40),
                  datetime(2022, 6, 26, 10, 0)],
            'temperature': [52.935, 53.1103, 53.0179, 53.4],
            'average_wind': [0.2275, 0.6385, 0.3333, 0.0],
        })

        # Daily data
        rsdata = stations.read_daily_data("Outdoor", ["rain_daily"],
                                          date(2022, 6, 25),
                                          date(2022, 6, 28))
        roundoff_floats(rsdata)
        self.assertEqual(rsdata, {
            'rain_daily': [1.232, 0.472],
            't':          [date(2022, 6, 26),
                           date(2022, 6, 27)]
        })

        # from pprint import pprint
        # pprint(rsdata)

    def test_compaction(self):
        """Compact a year's worth of stationname-yyyy-mm-dd.csv files
           into a single file with one entry per day.
        """
        pass


if __name__ == '__main__':
    unittest.main()

