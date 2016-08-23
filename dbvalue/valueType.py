import json
from dbvalue.util import util
import re
import urllib2

from stanfordnlp.stanfordAPI import StanfordAPI

class valueType():

    @staticmethod
    def number(value, nameColumn, dictionary):
        """ Checks whether a number is likely to be a coordinate

        Args:
            value: the value to analysis
            nameColumn: the name of the column of the value

        Returns:
            None: the value is not a number
            Value: the value is probably a coordinate and it is returned with the following format
                                    {"value": value, "key": value}
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
                    return ( "single", res, long(value) ) if res else None #("single", nameColumn, str(value))

                # For coordinates
                if -180 < num < 180:
                    res = util.findValue(nameColumn, dictionary, "dict_num")

                    if res:
                        return "single", res, num #{"value": num, "key": res}

                    if util.filterCoordinates(str(num)):
                        return "single", nameColumn, num #{"value": num, "key": nameColumn}

            return []


    @staticmethod
    def word(value, nameColumn, dictionary):
        """ Checks whether a word is likely to be a name related with location

        Args:
            value: the value to analysis
            nameColumn: the name of the column of the value

        Returns:
            None: the value is not related
            Value: the value is probably a location
        """
        # res = util.findValue(nameColumn, dictionary, "dict_str")
        # if res:
        #     return "single","text", value  #{"value": value, "key": "text"}

        #stanford npl library
        # if StanfordAPI.getLocations(value):
        #     return "single","text", value

        return None

    @staticmethod
    def json(value):
        """Checks whether value is a json file, if yes it looks for gps coordinates

        Args:
            value: the value that has to be checked.

        Returns:
            None: either the value is not a json or no values found.
            list: a list that contains the data found using the following format
                            {"latitude": value, "longitude":value, "datetime":value}

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

            if data: return "multiple", data

        return None

    @staticmethod
    def url(value):
        res = re.findall(r"(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)q=([-a-zA-Z0-9@:%_\+.~#?//=]*)",value)

        q = str(urllib2.unquote(res[0].split("&")[0].replace("+"," ")).decode('utf8')) if res else None

        return ( "single", "text", q ) if q else None


    @staticmethod
    def text(value):
        # if StanfordAPI.getLocations(value):
        #     return "single","text", value
        return None