"""
Appfun is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

Appfun is a class where new function can be added to extract geodata from specific apps.


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

from fileHandle import FileHandler

import re
import urllib2
import calendar

from org.sleuthkit.autopsy.casemodule import Case


class appfun:
    """Container for specific functions to extract Geodata.

    It is possible to add a new static method here and specify that on the XML file.
    The method has to have only one argument that is a list of file requested to the FileManager.

    See the Google Maps example:
        - the function is called 'googlemaps' and accepts one argument called 'files'.
        - on the XML file:

                <app>
                    <name>googlemaps</name>
                    <path>/data/com.google.android.apps.maps/cache/http</path>
                    <filename>%.0</filename>
                </app>

            'name' is the name of the function.
            'path' and 'filename' are the path and the name of the file where geodata has to be extracted.
    """

    #To extract geodata from Google Maps
    @staticmethod
    def googlemaps(files):

        data = []

        for file in files:

            handler = FileHandler(file, file.getNameExtension(), file.getName(), file.getUniquePath(), file.getId())

            if handler.store_file(Case.getCurrentCase().getTempDirectory()):

                fileobj = {"file":file, "el":[]}

                try:
                    with open(handler.getlclPath()) as f:
                        value = {}
                        for line in f:
                            if line.startswith("http"):

                                res = re.findall(r"(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)text=([-a-zA-Z0-9@:%_\+.~#?//=]*)",line)

                                q = str(urllib2.unquote(res[0].split("&")[0].replace("+"," ")).decode('utf8')) if res else None

                                if q:
                                    lat = re.findall(r"latitude_e7:\s*([+\-]?[0-9]*)",q)
                                    lng = re.findall(r"longitude_e7:\s*([+\-]?[0-9]*)",q)


                                    value["path"] = handler.getPath()
                                    value["name"] = handler.getName()

                                    #/10000000 is because of google's method to avoid the float point
                                    value["latitude"] = float(lat[0])/10000000
                                    value["longitude"] = float(lng[0])/10000000

                            if line.startswith("Date"):
                                res = line.split(", ")[1].split(" ")
                                m = {v: k for k,v in enumerate(calendar.month_abbr)}[res[1]]
                                datetime = res[2]+"-"+str(m)+"-"+res[0]+"T"+res[3]+"Z"
                                value["datetime"] = datetime

                        if value:
                            fileobj["el"].append(value)

                except:
                    pass

                data.append(fileobj)

        return data


    ####################################
    # Here a new function can be added #
    ####################################

    # @staticmethod
    # def namefunction(files):
    #     return None