"""
util is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

util is a class that collects useful methods.


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

import re


class util:
    """It contains useful methods"""

    @staticmethod
    def findValue(value, dict, typedict):
        """ Looks for a value in a json dictionary

        Args:
            value: value to look for
            dict: the dictionary loaded previously
            typedict: 'dict_num', 'dict_str', 'dict_datetime', 'dict_db' are the dictionaries available.

        Returns:
            None: no match in the dictionary
            Value: type of the value (latitude, logitude, datetime, text ..)
        """

        for x in dict[typedict]:
            if any(z.lower() == value.lower() for z in dict[typedict][x]):
                return x
        return None

    @staticmethod
    def isOneWord(value):
        """Checks whether the value is only one word

        Args: -

        Returns:
            True: it is
            False: it is not
        """

        list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '"', '%', '$', "'", '&', ')', '(', '+', '*', '-', ',', '/', '.', ';', ':', '=', '<', '?', '>',
                '@', '[', ']', '\\', '_', '^', '`', '{', '}', '|', '~']

        return False if any(char in list for char in value) else True

    @staticmethod
    def isNumber(value):
        """Checks whether the value is a number

        Args: -

        Returns:
            True: it is
            False: it is not
        """

        list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '.', '+', '-']

        return True if all(char in list for char in value) else False

    @staticmethod
    def noBlankSpace(value):
        """Checks whether there are blank spaces

        Args: -

        Returns:
            True: no blank spaces
            False: blank spaces
        """

        return False if any(char == " " for char in value) else True

    @staticmethod
    def filterCoordinates(value):
        """ Checks whether the value has a fractional-part with at least 5 digits

        Args:
            value: a number in string

        Returns:
            True: the value has a fractional-part with at least 5 digits
            False: the value doesn't have
        """
        return True if len(re.findall("[\.,](?=\d{5})", value)) == 1 else False