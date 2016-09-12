"""
util is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

util is a class that collects useful methods.


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