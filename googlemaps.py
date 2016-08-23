from fileHandle import FileHandler
from org.sleuthkit.autopsy.casemodule import Case
import re
import urllib2

class appmod:

    path = '/data/com.google.android.apps.maps/cache/http'

    name = '%.0'

    @staticmethod
    def process(files):

        for file in files:

            data = []

            handler = FileHandler(file, file.getNameExtension(), file.getName(), file.getUniquePath())

            if handler.store_file(Case.getCurrentCase().getTempDirectory()):

                try:
                    with open(handler.getLclPath()) as f:
                        for line in f:
                            res = re.findall(r"(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)text=([-a-zA-Z0-9@:%_\+.~#?//=]*)",value)

                            q = str(urllib2.unquote(res[0].split("&")[0].replace("+"," ")).decode('utf8')) if res else None

                            if q:
                                data.appand("{'path':"+handler.getPath()+", 'name':"+handler.getName()+", 'text':"+q+" }")

                except:
                    pass


        return data