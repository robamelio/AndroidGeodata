"""
stanfordAPI is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

stanfordAPI is a collections of methods useful to interact with stanford npl library.


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
import json
import urllib2

class StanfordAPI:
    """APIs to interact with Staford npl local server"""

    # java -mx5g -cp "./*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer

    @staticmethod
    def getLocations(value):
        """ Sends text to the parser and checks the response.

        Args:
            value: text to send to the Stanford library

        Returns:
            None: no locations found
            String: the word which should be a location
        """

        obj = StanfordAPI.parse_text(value)
        if obj:
            res = []
            for y in obj["sentences"]:
                for x in y["tokens"]:
                    if x["ner"] == "LOCATION":
                        res.append(x["word"])
            if res:
                return res
        return None

    @staticmethod
    def parse_text(text):
        """ Interacts with the Standford library.

        Args:
            value: text to send to the Stanford library

        Returns:
            None: no response from the library
            Json: result of the analysis of the text by Stanford library
        """

        if text:
            if text != "":
                url = 'http://127.0.0.1:9000/?properties=%7B%22annotators%22:%20%22tokenize,ner%22,%20%22outputFormat%22:%20%22json%22%7D'
                #annotators --> tokenize (sentence split up in many words in a smart way), ner (indentify the entity loc, name etc .. it requires tokenize)
                try:
                    handler  = urllib2.Request( url=url, data=text);
                    handler = urllib2.urlopen(handler)
                    response = handler.read().decode( 'utf-8' )
                    response = json.loads( response.replace('\r\n', ''), strict=False )
                    return response
                except:
                    return None

        return None
