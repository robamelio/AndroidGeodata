
from fileHandle import FileHandler
from dbvalue.timestamp import timestamp
from dbvalue.util import util
import inspect
import json
import os
import xml.dom.minidom

from java.util.logging import Level
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.datamodel import TskData
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException
from org.sleuthkit.autopsy.ingest import FileIngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import ModuleDataEvent
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.casemodule.services import Blackboard
import xml.etree.cElementTree as et

# import magicrobi
# f = magicrobi.Magic(magic_file="magic/magic")
# self.log(Level.INFO, "Format = "+f.from_file(file.getlclPath()))

# Factory that defines the name and details of the module and allows Autopsy
# to create instances of the modules that will do the anlaysis.
class AndroidGeodataCrawlerFactory(IngestModuleFactoryAdapter):

    moduleName = "Android Geodata Crawler"

    def getModuleDisplayName(self):
        return self.moduleName

    def getModuleDescription(self):
        return "Sample module that files large files that are a multiple of 4096."

    def getModuleVersionNumber(self):
        return "1.0"

    # Return true if module wants to get called for each file
    def isFileIngestModuleFactory(self):
        return True

    # can return null if isFileIngestModuleFactory returns false
    def createFileIngestModule(self, ingestOptions):
        return AndroidGeodataCrawler()


# File-level ingest module.  One gets created per thread.
class AndroidGeodataCrawler(FileIngestModule):

    _logger = Logger.getLogger(AndroidGeodataCrawlerFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    # Where any setup and configuration is done
    # 'context' is an instance of org.sleuthkit.autopsy.ingest.IngestJobContext.
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_ingest_job_context.html
    # TODO: Add any setup code that you need here.
    def startUp(self, context):
        # Counters
        self.jobId = context.getJobId()
        self.filesFound = 0
        self.dbFound = 0
        self.picFound = 0
        self.jsonFound = 0

        self.lastFile_rep = ''
        self.el_rep = None

        self.lastFile = ''
        self.el = None

        # Inits the xml element
        self.root = et.Element("androidgeodata")
        self.root_report = et.Element("report")
        # File where the xml is stored
        self.xmlname = os.path.join( Case.getCurrentCase().getReportDirectory(), Case.getCurrentCase().getName()+"_"+str(self.jobId))

        # Checks whether the JSON file exists, if not the module doesn't run
        path_to_dict = os.path.dirname(os.path.abspath(__file__)) + '/dictionary.json'
        if not os.path.exists(path_to_dict):
            raise IngestModuleException("The dictionary file was not found in module folder")
        else:
            # TODO: update this with XML scheme
            try:
                f = open(path_to_dict)
                self.dict = json.load(f)
            except: raise IngestModuleException("The dictionary file was not loaded")

    # Where the analysis is done.  Each file will be passed into here.
    # The 'file' object being passed in is of type org.sleuthkit.datamodel.AbstractFile.
    def process(self, file):

        # Use blackboard class to index blackboard artifacts for keyword search
        blackboard = Case.getCurrentCase().getServices().getBlackboard()

        # Skip non-files
        if ((file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNALLOC_BLOCKS) or
                (file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNUSED_BLOCKS) or
                (file.isFile() == False)):
            return IngestModule.ProcessResult.OK

        # Counts files found
        self.filesFound += 1

        # Inits variables
        data = []
        ext = file.getNameExtension()

        # Supported picture extensions
        if ext in ("jpg","jpeg","png"):
            ext = "pic"

        # Supported db extensions
        if ext in ("db","sqlite","sqlite3","db3"):
            ext = "db"

        # Analysis only the files with 'db',
        if ext in ("", "db", "pic", "json"):
        #if ext == "db":
            # Handles the file
            handler = FileHandler(file, file.getNameExtension(), file.getName(), file.getUniquePath() )

            # Stores the file
            if handler.store_file(Case.getCurrentCase().getTempDirectory()):
                # Bool value to check whether the file has been analysed to stop other controls
                bool = True

                # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                #                                                     #
                # At the moment supported files are: db, pic or json. #
                #                                                     #
                # # # # # # # # # # # # # # # # # # # # # # # # # # # #

                # is the file a db?
                if ( ext == "db" or ext == "" ) and not (util.findValue(handler.getName(),self.dict,"dict_db")):
                #if file.getName() == "CachedGeoposition.db":
                    #self.log(Level.INFO, "Processing DB: " + handler.getName())
                    self.dbFound += 1

                    # Tries a connection to verify whether the file is a db
                    if handler.connect():
                        # It means the file is a db
                        bool = False

                        tables = handler.getTables()
                        if tables:
                            for table in tables:
                                resultSet = handler.query(table)
                                try:
                                    resultSetMetaData = resultSet.getMetaData()
                                    numColumns = resultSetMetaData.getColumnCount()
                                except:
                                    resultSetMetaData = None
                                    numColumns = None

                                if (resultSet and resultSetMetaData and numColumns): #!= None:
                                    rows = []
                                    while resultSet.next():
                                        attributes = {}

                                        columns = range(1, numColumns + 1 )

                                        for column in columns:

                                            try:
                                                nameColumn = resultSetMetaData.getColumnName(column)
                                            except:
                                                nameColumn = None

                                            if nameColumn:
                                                temp = handler.processDB(resultSet, column, nameColumn, self.dict)
                                                if temp:
                                                    if temp[0] == "single":
                                                        attributes[temp[1]] = temp[2]
                                                        attributes["name"] = handler.getName()
                                                        attributes["type"] = "db"
                                                        attributes["table"] = table
                                                        attributes["path"] = handler.getPath()
                                                        if temp[1] in ("latitude", "longitude", "datetime", "text"):
                                                            attributes["column_"+temp[1]] = nameColumn
                                                        else:
                                                            if "column_other" in attributes:

                                                                attributes["column_other"].append(nameColumn)
                                                            else:
                                                                attributes["column_other"] = []
                                                                attributes["column_other"].append(nameColumn)


                                                    if temp[0] == "multiple":
                                                        if temp[1]:
                                                            for x in temp[1]:
                                                                x["name"] = handler.getName()
                                                                x["table"] = table
                                                                x["type"] = "db"
                                                                x["path"] = handler.getPath()
                                                                x["column"] = nameColumn
                                                            rows = rows + temp[1]


                                        if attributes: rows.append(attributes)

                                    if rows: data = data + rows

                            handler.close()

                # the file is not a db, is it a pic then?
                if (ext == "pic" or ext == "") and bool:
                    #self.log(Level.INFO, "Processing pic: " + handler.getName())
                    self.picFound += 1

                    res = handler.processPic()
                    if res:
                        res["name"] = handler.getName()
                        res["path"] = handler.getPath()
                        res["type"] = "pic"
                        data.append(res)
                        bool = False

                # The file is not a pic either, is it a file json?
                if (ext == "json" or ext == "") and bool:
                    #self.log(Level.INFO, "Processing json: " + handler.getName())
                    self.jsonFound += 1

                    if bool:
                        res = util.jsonFile(open(handler.getlclPath()))
                        if res:
                            for x in res:
                                x["name"] = handler.getName()
                                x["path"] = handler.getPath()
                                x["type"] = "json"

                            data += res

                # Deletes the file temporarily stored
                handler.delete_file()

        if data:
            #self.log(Level.INFO, "[File: "+handler.getName()+", "+str(data)+"]")
            el = None
            el_rep = None
            for item in data:

                if "latitude" and "longitude" in item:
                    self.log(Level.INFO, "[File: "+handler.getName()+", "+str(data)+"]")

                    # if self.lastFile == item["name"]:
                    #     # Element already exists
                    #     if not any(table.get("name") == item["table"] for table in self.el.find("tables").iter("table") ):
                    #         #No table
                    #         table = et.SubElement(self.el.find("tables"), "table", name=item["name"])
                    #         if "column" in item:
                    #             et.SubElement(table,"column", type="").text = item["column"]
                    #         else:
                    #             et.SubElement(table,"column", type="latitude").text = item["column_latitude"]
                    #             et.SubElement(table,"column", type="longitude").text = item["column_longitude"]
                    #             if "column_datetime" in item:
                    #                 et.SubElement(table,"column", type="datetime").text = item["column_datetime"]
                    #
                    # else:
                    #     # No element
                    #     el = et.SubElement(self.root, item["type"])
                    #     et.SubElement(el, "app").text = item["path"] #.split("\/")[-2]
                    #     et.SubElement(el, "path").text = item["path"]
                    #     et.SubElement(el, "name").text = item["name"]
                    #     if "table" in item:
                    #         tables = et.SubElement(el, "tables")
                    #         table = et.SubElement(tables, "table", name=item["table"])
                    #         if "column" in item:
                    #             et.SubElement(table,"column", type="").text = item["column"]
                    #         else:
                    #             et.SubElement(table,"column", type="latitude").text = item["column_latitude"]
                    #             et.SubElement(table,"column", type="longitude").text = item["column_longitude"]
                    #             if "column_datetime" in item:
                    #                 et.SubElement(table,"column", type="datetime").text = item["column_datetime"]
                    #
                    #     self.el = el
                    #
                    # self.lastFile = item["name"]

                    if not el:
                        # No element
                        el = et.SubElement(self.root, item["type"])
                        et.SubElement(el, "app").text = item["path"] #.split("\/")[-2]
                        et.SubElement(el, "path").text = item["path"]
                        et.SubElement(el, "name").text = item["name"]
                        if "table" in item:
                            tables = et.SubElement(el, "tables")
                            table = et.SubElement(tables, "table", name=item["table"])
                            if "column" in item:
                                et.SubElement(table,"column", type="").text = item["column"]
                            else:
                                et.SubElement(table,"column", type="latitude").text = item["column_latitude"]
                                et.SubElement(table,"column", type="longitude").text = item["column_longitude"]
                                if "column_datetime" in item:
                                    et.SubElement(table,"column", type="datetime").text = item["column_datetime"]
                    else:
                        #Element already exists
                        if not any(table.get("name") == item["table"] for table in el.find("tables").iter("table") ):
                            #No table
                            table = et.SubElement(el.find("tables"), "table", name=item["name"])
                            if "column" in item:
                                et.SubElement(table,"column", type="").text = item["column"]
                            else:
                                et.SubElement(table,"column", type="latitude").text = item["column_latitude"]
                                et.SubElement(table,"column", type="longitude").text = item["column_longitude"]
                                if "column_datetime" in item:
                                    et.SubElement(table,"column", type="datetime").text = item["column_datetime"]


                    art = file.newArtifact(BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACKPOINT)

                    if "datetime" in item:
                        if item["datetime"] != "":
                            if isinstance(item["datetime"],str):
                                if ext == "pic":
                                    att3 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DATETIME.getTypeID(),
                                                               AndroidGeodataCrawlerFactory.moduleName, timestamp.getTimestampFromPicDatetime(item["datetime"]) )
                                else:
                                    att3 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DATETIME.getTypeID(),
                                                               AndroidGeodataCrawlerFactory.moduleName, timestamp.getTimestampFromString(item["datetime"]) )
                            else:
                                att3 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DATETIME.getTypeID(),
                                                           AndroidGeodataCrawlerFactory.moduleName,  timestamp.epochTOtimestamp(item["datetime"]))

                            art.addAttribute(att3)

                    att1 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_GEO_LATITUDE.getTypeID(),
                                               AndroidGeodataCrawlerFactory.moduleName, item["latitude"])

                    att2 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_GEO_LONGITUDE.getTypeID(),
                                               AndroidGeodataCrawlerFactory.moduleName, item["longitude"])

                    att4 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_PROG_NAME.getTypeID(),
                                               AndroidGeodataCrawlerFactory.moduleName, item["name"])

                    art.addAttributes([att1, att2, att4])

                    if "column" in item:
                        att5 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DESCRIPTION.getTypeID(),
                                                   AndroidGeodataCrawlerFactory.moduleName, "table: "+item["table"]+", column = "+item["column"])
                        art.addAttribute(att5)
                    elif "table" in item:
                        att5 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DESCRIPTION.getTypeID(),
                                                   AndroidGeodataCrawlerFactory.moduleName, "table: "+item["table"]+", column = "+item["column_latitude"]+", "+item["column_longitude"])
                        art.addAttribute(att5)

                    try:
                        # index the artifact for keyword search
                        blackboard.indexArtifact(art)
                    except Blackboard.BlackboardException as e:
                        self.log(Level.SEVERE, "Error indexing artifact " + art.getDisplayName())

                    return IngestModule.ProcessResult.OK


                if "text" in item:

                    art_text = file.newArtifact(blackboard.getOrAddArtifactType("geodataTEXT","Geodata in text").getTypeID())
                    att = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_TEXT.getTypeID(),
                                              AndroidGeodataCrawlerFactory.moduleName, item["text"] )
                    if "column_text" and "table" in item:
                        att1 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DESCRIPTION.getTypeID(),
                                                   AndroidGeodataCrawlerFactory.moduleName, "table: "+item["table"]+", column = "+item["column_text"])

                    art_text.addAttributes([att,att1])

                    try:
                        # index the artifact for keyword search
                        blackboard.indexArtifact(art_text)
                    except Blackboard.BlackboardException as e:
                        self.log(Level.SEVERE, "Error indexing artifact " + art_text.getDisplayName())


                if "column_other" in item:
                    # if self.lastFile_rep == item["name"]:
                    #     # Element already exists
                    #     #if any(table.get("name") == item["name"] for table in self.el.iter("table") ):
                    #     t = True
                    #
                    #     for table in self.el_rep.find("tables").iter("table"):
                    #         if table.get("name") == item["table"]:
                    #             #Table already exists
                    #             t = False
                    #             for column in item["column_other"]:
                    #                 if not any(c.text == column for c in table.iter("column")):
                    #                     et.SubElement(table, "column").text = column
                    #             #break
                    #     if t:
                    #         #No table
                    #         table = et.SubElement(self.el_rep.find("tables"), "table", name=item["table"])
                    #         for column in item["column_other"]:
                    #             et.SubElement(table,"column", type="").text = column
                    #
                    # else:
                    #     # No element
                    #     el_rep = et.SubElement(self.root_report, item["type"])
                    #     et.SubElement(el_rep, "app").text = item["path"] #.split("\/")[-2]
                    #     et.SubElement(el_rep, "path").text = item["path"]
                    #     et.SubElement(el_rep, "name").text = item["name"]
                    #     tables = et.SubElement(el_rep, "tables")
                    #     table = et.SubElement(tables, "table", name=item["table"])
                    #     for column in item["column_other"]:
                    #         et.SubElement(table,"column", type="").text = column
                    #
                    #     self.el_rep = el_rep
                    #
                    # self.lastFile_rep = item["name"]

                    if not el_rep:
                        # No element
                        el_rep = et.SubElement(self.root_report, item["type"])
                        et.SubElement(el_rep, "app").text = item["path"] #.split("\/")[-2]
                        et.SubElement(el_rep, "path").text = item["path"]
                        et.SubElement(el_rep, "name").text = item["name"]
                        tables = et.SubElement(el_rep, "tables")
                        table = et.SubElement(tables, "table", name=item["table"])
                        for column in item["column_other"]:
                            et.SubElement(table,"column", type="").text = column
                    else:
                        # Element already exists
                        #if any(table.get("name") == item["name"] for table in self.el.iter("table") ):
                        t = True

                        for table in el_rep.find("tables").iter("table"):
                            if table.get("name") == item["table"]:
                                #Table already exists
                                t = False
                                for column in item["column_other"]:
                                    if not any(c.text == column for c in table.iter("column")):
                                        et.SubElement(table, "column").text = column
                                        #break
                        if t:
                            #No table
                            table = et.SubElement(el_rep.find("tables"), "table", name=item["table"])
                            for column in item["column_other"]:
                                et.SubElement(table,"column", type="").text = column









            # Fire an event to notify the UI and others that there is a new artifact
            IngestServices.getInstance().fireModuleDataEvent(
            ModuleDataEvent(AndroidGeodataCrawlerFactory.moduleName,
            BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACKPOINT, None))

        return IngestModule.ProcessResult.OK


    #def results():

    # Where any shutdown code is run and resources are freed.
    # TODO: Add any shutdown code that you need here.
    def shutDown(self):
        self.log(Level.INFO, str(xml.dom.minidom.parseString(et.tostring(self.root)).toprettyxml()))

        self.log(Level.INFO, str(xml.dom.minidom.parseString(et.tostring(self.root_report)).toprettyxml()))

        self.xmlname += "_"+str(self.picFound)+str(self.dbFound)+str(self.jsonFound)+str(self.filesFound)+"_androidgeodata.xml"

        report = open(self.xmlname, 'w')
        #report.write(str(xml.dom.minidom.parseString(et.tostring(self.root)+"<!-- Reporto possible other coordinates --> "+et.tostring(self.root_report)).toprettyxml()))
        report.close()
        Case.getCurrentCase().addReport(self.xmlname, AndroidGeodataCrawlerFactory.moduleName, "AndroidGeodata XML")
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA, AndroidGeodataCrawlerFactory.moduleName,
             "In this thread: "+str(self.filesFound)+" files found, "+str(self.picFound)+" pictures, "+str(self.dbFound)+" DBs and "+str(self.jsonFound)+" json processed. \n A xml ("+self.xmlname+") and a report have been created ")
        IngestServices.getInstance().postMessage(message)
        #None