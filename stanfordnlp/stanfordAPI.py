"""
stanfordAPI is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

stanfordAPI is a collections of methods useful to interact with stanford npl library.


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
                # annotators:
                #   tokenize = sentence split up in many words in a smart way.
                #   ner = identify the entity (location, Name etc.), it requires tokenize.

                url = 'http://127.0.0.1:9000/?properties=%7B%22annotators%22:%20%22tokenize,ner%22,%20%22outputFormat%22:%20%22json%22%7D'
                try:
                    handler  = urllib2.Request( url=url, data=text);
                    handler = urllib2.urlopen(handler)
                    response = handler.read().decode( 'utf-8' )
                    #response = json.loads( response.replace('\r\n', ''), strict=False )
                    response = json.loads( response)
                    return response
                except:
                    return None

        return None
