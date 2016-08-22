import os

from java.io import File
from java.lang import Class
from java.sql import DriverManager
from org.sleuthkit.autopsy.datamodel import ContentUtils

import exif
from dbvalue.util import util
from dbvalue.valueType import valueType
from pil import Image


class FileHandler:
    """ It handles a file: storing, deleting, processing of data and DB connection management.

    Attributes:
        file: it's the file.
        extension: it's the extension of the file.
    """

    def __init__(self, file, extension, name, path):
        """Inits FileHandler."""
        self.file = file
        self.extension = extension
        self.path = path
        self.name = name
        self.lclPath = ""
        self.dbConn = None
        self.stmt = None

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
            True: file stored
            false: errors in storing the file
        """
        try:
            self.lclPath = os.path.join(directory, self.file.getName())
            ContentUtils.writeToFile(self.file, File(self.lclPath))
        except:
            return False
        else:
            return True

    def delete_file(self):
        """ Deletes the file stored when it's been precessed.

        Args: -

        Returns:
            True: file deleted.
            False: errors in deleting the file.
        """
        try:
            os.remove(self.lclPath)
        except:
            return False
        else:
            return True

    def processPic(self):
        """ Looks for geodata in EXIF.

        Args: -

        Returns:
            None: when either the pic is not open or no geodata is found.
            data: data with geodata represented as {"latitude": value, "longitude": value, "datetime": value}
        """
        try:
            image = Image.open(self.lclPath)
        except:
            return None
        else:
            exif_data = exif.get_exif_data(image)
            data = exif.get_lat_lon_datatime(exif_data)
            if data:
                if data["latitude"] != "" and data["longitude"] != "":
                    return data


    def processFile(self):
        """

        :return:
        """
        try:
            with open(self.lclPath) as f:
                for line in f:
                    # process(line)
                    pass
        except: return None

    def connect(self):
        """ Connects to the databased stored with the method 'stored_file'.

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
            None: no value found
            list:

        """

        try:
            value = resultSet.getString(column)
            value = value.encode('ascii', 'ignore')
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
                    return valueType.word(value,nameColumn, dictionary)

                #Json
                if value.startswith("{"):
                    return valueType.json(value,)

                #Http
                if util.noBlankSpace(value):
                    return valueType.url(value)

                #Text
                return valueType.text(value)

            return None




