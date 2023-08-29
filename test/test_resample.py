#!/usr/bin/env python3

import unittest

import sys
sys.path.insert(0, 'server')

import stations
from watchserver import plot

from datetime import datetime, date, timedelta

from shutil import rmtree

import os


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
        stations.savedir = "test/files/rawdata"

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
                             't': [datetime(2022, 6, 25, 23, 0),
                                   datetime(2022, 6, 25, 23, 20),
                                   datetime(2022, 6, 26, 0, 0),
                                   datetime(2022, 6, 26, 0, 20),
                                   datetime(2022, 6, 26, 0, 40),
                                   datetime(2022, 6, 26, 1, 0)],
                             'temperature': [53.095, 52.865, 52.59,
                                             52.92, 53.085, 53.1]
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
                                   datetime(2022, 6, 28, 0, 0),
                                   datetime(2022, 6, 28, 0, 20),
                                   datetime(2022, 6, 28, 0, 40),
                                   datetime(2022, 6, 28, 1, 0)],
                             'temperature': [53.5385, 52.86, 52.55,
                                             53.5585, 53.3325, 52.7]
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
            't':          [date(2022, 6, 25),
                           date(2022, 6, 26),
                           date(2022, 6, 27),
                           date(2022, 6, 28)
                           ]
            'rain_daily': [0.559, 1.232, 0.472, 0.0],
        })

    def test_compaction(self):
        datadir = "test/files/rawdata"
        stations.savedir = "test/files/compact"
        try:
            rmtree(stations.savedir)
        except FileNotFoundError:
            pass
        try:
            os.mkdir(stations.savedir)
        except FileExistsError:
            pass

        self.assertTrue(os.path.exists(stations.savedir))

        # print("Initially savedir looks like")
        # os.system(f"ls -lR {stations.savedir}")

        # Make savedir initially a mirror of datadir.
        # Uses hard links; for hard links, use os.symlink() instead,
        # but then you have to worry about how many .. to use.
        orig_files = []
        for f in os.listdir(datadir):
            if not f.startswith('Outdoor-2022-'):
                continue
            os.link(os.path.join(datadir, f),
                    os.path.join(stations.savedir, f))
            orig_files.append(f)

        orig_files.sort()

        archivedir = os.path.join(stations.savedir, "archived")
        try:
            rmtree(archivedir)
        except:
            pass

        stationname = "Outdoor"
        stations.compact_stations(stationname)

        cached_files = sorted( [ f for f in os.listdir(stations.savedir)
                                 if f.endswith('.csv') ] )
        self.assertEqual(cached_files, [
            "Outdoor-2022-01-hourly.csv",
            "Outdoor-2022-02-hourly.csv",
            "Outdoor-2022-03-hourly.csv",
            "Outdoor-2022-04-hourly.csv",
            "Outdoor-2022-05-hourly.csv",
            "Outdoor-2022-06-hourly.csv",
            "Outdoor-2022-daily.csv"
        ])
        archived_files = sorted(os.listdir(archivedir))
        self.assertEqual(archived_files, orig_files)

        # XXX Check contents of files here

        # Now make sure plot() can make a plot from the archived data
        # plot(stationname, date(2022, 1, 1), date(2022, 7, 1))

        # Remove the working directory
        rmtree(stations.savedir)


if __name__ == '__main__':
    unittest.main()

