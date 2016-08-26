from fileHandle import FileHandler
from org.sleuthkit.autopsy.casemodule import Case
import re
import urllib2

class appfun:

    @staticmethod
    def googlemaps(files):

        data = []

        for file in files:



            handler = FileHandler(file, file.getNameExtension(), file.getName(), file.getUniquePath())

            if handler.store_file(Case.getCurrentCase().getTempDirectory()):

                fileobj = {"file":file, "el":[]}

                try:
                    with open(handler.getlclPath()) as f:
                        for line in f:
                            res = re.findall(r"(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)text=([-a-zA-Z0-9@:%_\+.~#?//=]*)",line)

                            q = str(urllib2.unquote(res[0].split("&")[0].replace("+"," ")).decode('utf8')) if res else None

                            if q:
                                lat = re.findall(r"latitude_e7:\s*([+\-]?[0-9]*)",q)
                                lng = re.findall(r"longitude_e7:\s*([+\-]?[0-9]*)",q)

                                value = {}
                                value["path"] = handler.getPath()
                                value["name"] = handler.getName()
                                value["latitude"] = float(lat[0])/10000000
                                value["longitude"] = float(lng[0])/10000000

                                fileobj["el"].append(value)
                except:
                    pass

                data.append(fileobj)



        return data