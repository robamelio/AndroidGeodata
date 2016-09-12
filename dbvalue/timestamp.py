"""
timestamp is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

timestamp is a class that collects methods to manage the conversion among the different date formats.


Copyright (C) 2016  Roberto Amelio

This file is part of AndroidGeodata.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import datetime
import time

class timestamp:
    """It contains useful methods"""

    @staticmethod
    def getTimestampFromString(value):
        """ Converts from ISO 8601 to epoch timestamp.
            ISO 8601 defines the international standard representation of dates and times.

        Args:
            value: date and time in ISO 8601 format

        Returns:
            None: error during the conversion
            Timestamp
        """

        try:
            d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        except:
            return None
        else:
            return int(time.mktime(d.timetuple()))

    @staticmethod
    def getTimestampFromPicDatetime(value):
        """ Converts from DateTime extracted from a pic to epoch timestamp.

        Args:
            value: date and time from pic

        Returns:
            Timestamp
        """
        date = value.split(" ")[0].split(":")

        time_var = value.split(" ")[1].split(":")

        d = datetime.datetime(year=int(date[0]),month=int(date[1]),day=int(date[2]),hour=int(time_var[0]),minute=int(time_var[1]),second=int(time_var[2]))

        return int(time.mktime(d.timetuple()))
