"""
timestamp is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

timestamp is a class that collects methods to manage the conversion among the different date formats.


Copyright (C) 2016  Roberto Amelio

This file is part of AndroidGeodata.

AndroidGeodata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

AndroidGeodata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with AndroidGeodata.  If not, see <http://www.gnu.org/licenses/>.
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
