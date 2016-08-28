"""
FileHandle is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

FileHandle is a class that manages a file, basically is an abstraction of
the Autopsy file given as input.


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

import exif
from dbvalue.util import util
from dbvalue.valueType import valueType
from stanfordnlp.stanfordAPI import StanfordAPI
from pil import Image

import os
import json

from java.io import File
from java.lang import Class
from java.sql import DriverManager
from org.sleuthkit.autopsy.datamodel import ContentUtils

class FileHandler:
    """ It handles a file: storing, deleting, processing data and DB connection management.

    Attributes:
        file: datamodel.AbstractContent file.
        extension: file's extension.
        name: file's name.
        path: file's path in the Android storage.
        id: file's id from AbstractContent.
        stanpl: flag for stanford npl library
    """

    def __init__(self, file, extension, name, path, id, stanpl=False):
        """Inits FileHandler"""
        self.file = file
        self.extension = extension
        self.path = path
        self.name = name
        self.id = id
        self.stanpl = stanpl
        self.lclPath = ""
        self.dbConn = None
        self.stmt = None
        self.storedName = str(self.id)+"."+self.extension if self.extension else str(self.id)

    def getName(self):
        """Returns the name of the file"""
        return self.name

    def getPath(self):
        """Returns the path of the file"""
        return self.path

    def getlclPath(self):
        """Returns the local path of the file"""
        return self.lclPath

    def isPic(self):
        """Checks the extension when the file is a picture.

        Args: -

        Returns:
            True: the extension is accepted.
            False: the extension is not supported.

        """
        return True if self.extension in ["jpg","png","jpeg"] else False


    def store_file(self, directory):
        """ Stores the file in the directory of the case (Usually in the directory 'temp')

        Args:
            directory: where to store the file.

        Returns:
            True: file stored.
            False: errors in storing the file.
        """
        try:
            self.lclPath = os.path.join(directory, self.storedName)
            ContentUtils.writeToFile(self.file, File(self.lclPath))
        except:
            return False
        else:
            return True

    def delete_file(self):
        """ Deletes a file stored.

        Args: -

        Returns:
            None: file deleted.
            String: the error if it fails.
        """
        try:
            os.remove(self.lclPath)
        except OSError as e:
            return str(e)
        else:
            return None

    def processPic(self):
        """ Looks for geodata in EXIF.

        Args: -

        Returns:
            None: when either the pic is not open or no geodata is found.
            data: data with geodata represented as {"latitude": value, "longitude": value, "datetime": value}.
        """
        try:
            image = Image.open(self.lclPath)
        except:
            return None
        else:
            exif_data = exif.get_exif_data(image)
            data = exif.get_lat_lon_datatime(exif_data)
            if data and (data["latitude"] != "" and data["longitude"] != ""):
                return data


    def processFile(self):
        """ Looks for words that may be related with locations using the stanford library

        Args: -

        Returns:
            String: line of the file where there is a location.
            None: no words found.
        """
        try:
            with open(self.lclPath) as f:
                for line in f:
                    line = line.encode('utf-8', 'ignore')
                    if StanfordAPI.getLocations(line):
                        return {"text":str(line)}
        except:
            pass

        return None

    def connect(self):
        """ Connects to a databased if the file being processed is a db.

        Args: -

        Returns:
            True: the connection is made
            False: no connection made
        """
        try:
            Class.forName("org.sqlite.JDBC").newInstance()
            self.dbConn = DriverManager.getConnection("jdbc:sqlite:%s" % self.lclPath)
        except:
            return False
        else:
            return True

    def query(self, table):
        """ Makes a SELECT on a specific table of the database.

        Args:
           table: name of the table in the database.

        Returns:
            Results: if the query succeeds, the results are returned
            None: errors in querying
        """
        try:
            self.stmt = self.dbConn.createStatement()
            return self.stmt.executeQuery("SELECT * FROM " + table)
        except:
            return None

    def getTables(self):
        """ Querys a database to get the name of all the tables

        Args: -

        Returns:
            it returns a list of the tables in the databases if the query succeeds, otherwise returns an empty list.

        """
        try:
            self.stmt = self.dbConn.createStatement()
            resultSet= self.stmt.executeQuery("SELECT name FROM sqlite_master WHERE type='table'")
        except:
            return []
        else:
            a = []
            while resultSet.next():
                try:
                    a.append(resultSet.getString("name"))
                except: pass
            return a


    def close(self):
        """ Closes the connection with a database

        Args: -

        Returns: -
        """
        try:
            self.stmt.close()
            self.dbConn.close()
        except:
            pass
        finally:
            self.stmt = None
            self.dbConn = None

    def processDB(self, resultSet, column, nameColumn, dictionary):
        """ Processes a single value in a table of a database

        Args:
            resultSet: results from previous queries.
            column: it identifies the column, it can be either a number or the name.
            nameColumn: name of the column.

        Returns:
            None: no value found.
            Value: the value matches.

        """

        try:
            value = resultSet.getString(column)
            #value = value.encode('ascii', 'ignore')
            value = value.encode('utf-8', 'ignore')
        except:
            return None
        else:
            if value and value != "":

                if util.isNumber(value):
                    #Number
                    res = valueType.number(value, nameColumn, dictionary)
                    if res != None:
                        return res if res else None

                if util.isOneWord(value):
                    #Word
                    return valueType.word(value,nameColumn, dictionary, self.stanpl)

                #Json
                if value.startswith("{"):
                    return valueType.json(value)

                #Http
                if util.noBlankSpace(value):
                    return valueType.url(value, self.stanpl)

                #Text
                if self.stanpl:
                    return valueType.text(value)

            return None

    def processJsonFile(self):
        """Checks whether value is a json file, if yes it looks for gps coordinates

        Args:
            value: the value that has to be checked.

        Returns:
            None: either the value is not a json or no values found.
            list: a list that contains the data found using the following format
                            {"latitude": value, "longitude":value, "datetime":value}

        """
        try:
            value = open(self.lclPath())
        except:
            return None
        else:
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
                    if data:
                        return data
                return None