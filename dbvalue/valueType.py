"""
ValueType is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

ValueType is a class where functions to manage values in a database are defined.


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

import json
from dbvalue.util import util
import re
import urllib2

from stanfordnlp.stanfordAPI import StanfordAPI


class valueType:

    @staticmethod
    def number(value, nameColumn, dictionary):
        """ Checks whether a number is likely to be a coordinate

        Args:
            value: the value to analysis.
            nameColumn: the name of the column of the value.
            dictionary: the dictionary to use.

        Returns:
            None: the value is not a number.
            Empty list: the value is a number but not a coordinate.
            List: the value is probably a coordinate and a list that contains:
                            ['single', nameColumn/'datetime'/'longitude'/'latitude', value]
        """
        # is it a number?
        try:
            num = float(value)
        except:
            return None
        else:
            if num != 0:

                # For datetime value
                if num > 1000000000:
                    res = util.findValue(nameColumn, dictionary, "dict_datetime")
                    return ( "single", res, long(value) ) if res else None

                # For coordinates
                if -180 < num < 180:
                    res = util.findValue(nameColumn, dictionary, "dict_num")

                    if res:
                        return "single", res, num

                    if util.filterCoordinates(str(num)):
                        return "single", nameColumn, num

            return []

    @staticmethod
    def word(value, nameColumn, dictionary, stanpl, strdict):
        """ Checks whether a word is likely to be a name related with locations

        Args:
            value: the value to analysis.
            nameColumn: the name of the column of the value.
            dictionary: the dictionary to use.
            stanpl: the flag for the stanford npl library.

        Returns:
            None: the value is not related.
            Value: the value is probably a location.
        """
        if stanpl:
            if StanfordAPI.getLocations(value):
                return "single","text", value
        elif strdict:
            res = util.findValue(nameColumn, dictionary, "dict_str")
            if res:
                return "single","text", value
        else:
            return "single","text", value

        return None

    @staticmethod
    def json(value):
        """Checks whether value is a json file, if yes it looks for gps coordinates

        Args:
            value: the value that has to be checked.

        Returns:
            None: either the value is not a json or no values found.
            list: a list that contains the data found using the following format
                            ['multiple', [{"latitude": value, "longitude":value, "datetime":value}]]
        """

        data_lat = []
        data_lng = []

        key = ["latitude","lat","longitude","lng"]

        def findkey(dct):
            try: data_lat.append(dct[key[0]])
            except KeyError:
                try: data_lat.append(dct[key[1]])
                except KeyError:pass
            return dct

        def extractlng(dct):
            try: data_lng.append(dct[key[2]])
            except KeyError:
                try: data_lng.append(dct[key[3]])
                except KeyError:pass
            return dct

        try:
            json.loads(value, object_hook=findkey)
        except ValueError: return None
        #TODO: look for the timestamp value?
        if data_lat:
            json.loads(value, object_hook=extractlng)
            data = []
            for x in range(0,len(data_lat)):
                data.append({"latitude": data_lat[x], "longitude":data_lng[x], "datetime":""})

            if data:
                return "multiple", data

        return None

    @staticmethod
    def url(value, stanpl):
        """Checks whether a url contains a research on locations looking for the keywork q=

        Args:
            value: the value that has to be checked.
            stanpl: flag for the Stanford npl library.

        Returns:
            None: no locations found.
            list: a list that contains the data found using the following format
                            ['single', 'text', value]
        """
        res = re.findall(r"(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)q=([-a-zA-Z0-9@:%_\+.~#?//=]*)",value)

        q = str(urllib2.unquote(res[0].split("&")[0].replace("+"," ")).decode('utf8')) if res else None

        if stanpl:
            if not StanfordAPI.getLocations(q):
                q = None

        return ( "single", "text", q ) if q else None


    @staticmethod
    def text(value):
        """Looks for words related to locations in text

        Args:
            value: the value that has to be checked.

        Returns:
            None: no words found.
            list: a list that contains the data found using the following format
                            ['single', 'text', value]
        """
        if StanfordAPI.getLocations(value):
            return "single","text", value
        return None