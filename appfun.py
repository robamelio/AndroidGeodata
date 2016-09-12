"""
Appfun is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

Appfun is a class where new function can be added to extract geodata from specific apps.


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