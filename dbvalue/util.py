import json
import re

from stanfordnlp.stanfordAPI import StanfordAPI

class util():
    """It contains al the methods used to extract and elaborate the information"""


    @staticmethod
    def findValue(value, dict, typedict):
        """ Looks for a value in a json dictionary

        Args:
            value: value to look for
            dict: the dictionary loaded previously
            typedict: 'dict_num' and 'dict_str' are the two dictionaries available.

        Returns:
            None: no match in the dictionary
            Value: type of the value (latitude, logitude, datetime, text ..)
        """

        # for x in dict[typedict]:
        #     for z in dict[typedict][x]:
        #         if value.lower() == z.lower():
        #             return x
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
        #'0', '1', '2', '3', '4', '5', '6', '7', '8', '9',

        list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '"', '%', '$', "'", '&', ')', '(', '+', '*', '-', ',', '/', '.', ';', ':', '=', '<', '?', '>',
                '@', '[', ']', '\\', '_', '^', '`', '{', '}', '|', '~']

        # list = ['!', '#', '"', '%', '$', "'", '&', ')', '(', '+', '*', '-', '/', ';', ':', '=', '<', '?', '>',
        #         '@', '[', ']', '\\', '_', '^', '`', '{', '}', '|', '~']
        return False if any(char in list for char in value) else True

    @staticmethod
    def isNumber(value):
        """Checks whether the value is only one word

        Args: -

        Returns:
            True: it is
            False: it is not
        """
        #'0', '1', '2', '3', '4', '5', '6', '7', '8', '9',

        list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '.', '+', '-']

        # list = ['!', '#', '"', '%', '$', "'", '&', ')', '(', '+', '*', '-', '/', ';', ':', '=', '<', '?', '>',
        #         '@', '[', ']', '\\', '_', '^', '`', '{', '}', '|', '~']
        return True if all(char in list for char in value) else False

    @staticmethod
    def noBlankSpace(value):
        """Checks whether there are blank spaces

        Args: -

        Returns:
            True: no blank spaces
            False: blank spaces
        """

        # By regular expression
        # return True if len(re.findall("\S+", value)) == 1 else False
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


    @staticmethod
    def jsonFile(value):
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
            json.load(value, object_hook=findkey)
        except:
            return None
        else:
            #TODO: look for the timestamp value?
            if data_lat:
                json.load(value, object_hook=extractlng)
                data = []
                for x in range(0,len(data_lat)):
                    data.append({"latitude": data_lat[x], "longitude":data_lng[x], "datetime":""})
                if data: return data
            return None















