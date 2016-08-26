import inspect
import os
import xml.etree.cElementTree as et
from fileHandle import FileHandler
from dbvalue.timestamp import timestamp
from dbvalue.util import util
import json
from org.sleuthkit.datamodel import TskCoreException
from appfun import appfun
from java.util.logging import Level
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.datamodel import SleuthkitCase
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import ModuleDataEvent
from org.sleuthkit.autopsy.coreutils import Logger

from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException
from org.sleuthkit.autopsy.casemodule.services import Blackboard

# from org.sleuthkit.autopsy.ingest import FileIngestModule
# from java.lang import System
# from org.sleuthkit.datamodel import AbstractFile
# from org.sleuthkit.datamodel import ReadContentInputStream
# import jarray
# from org.sleuthkit.autopsy.casemodule.services import Services
# from org.sleuthkit.autopsy.casemodule.services import FileManager


# Factory that defines the name and details of the module and allows Autopsy
# to create instances of the modules that will do the analysis.
# TODO: Rename this to something more specific. Search and replace for it because it is used a few times
class AndroidGeodataXMLFactory(IngestModuleFactoryAdapter):
    # TODO: give it a unique name.  Will be shown in module list, logs, etc.
    moduleName = "Android Geodata XML"

    def getModuleDisplayName(self):
        return self.moduleName

    # TODO: Give it a description
    def getModuleDescription(self):
        return "Sample module that does X, Y, and Z."

    def getModuleVersionNumber(self):
        return "1.0"

    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingestOptions):
        # TODO: Change the class name to the name you'll make below
        return AndroidGeodataXML()


# Data Source-level ingest module.  One gets created per data source.
# TODO: Rename this to something more specific. Could just remove "Factory" from above name.
class AndroidGeodataXML(DataSourceIngestModule):
    _logger = Logger.getLogger(AndroidGeodataXMLFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def __init__(self):
        self.context = None

    # Where any setup and configuration is done
    # 'context' is an instance of org.sleuthkit.autopsy.ingest.IngestJobContext.
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_ingest_job_context.html
    # TODO: Add any setup code that you need here.
    def startUp(self, context):
        self.context = context

        # Verify the xml is there and is correct before any ingest starts
        path_to_xml = os.path.dirname(os.path.abspath(__file__)) + '/geodata.xml'
        if not os.path.exists(path_to_xml):
            raise IngestModuleException("The xml file was not found in module folder")
        else:
            temp = open(path_to_xml)
            self.data_from_xml = temp.read()

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




        # if not os.path.exists(DataExtraction.path_to_dict):
        #     raise IngestModuleException("")



    # Where the analysis is done.
    # The 'dataSource' object being passed in is of type org.sleuthkit.datamodel.Content.
    # See: http://www.sleuthkit.org/sleuthkit/docs/jni-docs/4.3/interfaceorg_1_1sleuthkit_1_1datamodel_1_1_content.html
    # 'progressBar' is of type org.sleuthkit.autopsy.ingest.DataSourceIngestModuleProgress
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_data_source_ingest_module_progress.html
    def process(self, dataSource, progressBar):
        # TODO: keep updated the progressBar
        # we don't know how much work there is yet
        progressBar.switchToIndeterminate()

        # Use blackboard class to index blackboard artifacts for keyword search
        # TODO: check whether you really need this
        blackboard = Case.getCurrentCase().getServices().getBlackboard()


        # FileManager for the current case
        fileManager = Case.getCurrentCase().getServices().getFileManager()

        tree = et.fromstring(self.data_from_xml)
        numFiles = len(tree)
        progressBar.switchToDeterminate(numFiles)
        elCount = 0

        # TODO: remove blank spaces
        for el in tree:
            self.log(Level.INFO, "Element tag '" + el.tag+"'")
            # TODO: think where place this one
            # Check if the user pressed cancel while we were busy
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK


            data = []


            if el.tag == "pic":
                path = el.find("path").text.replace(" ","")

                files = fileManager.findFiles(dataSource, "%", path)
            if el.tag == "db":
                path = el.find("path").text.replace(" ","")
                name = el.find("name")
                if name is None:
                    files = fileManager.findFiles(dataSource, "%", path)
                else:
                    #files = fileManager.findFiles(dataSource, name.text.replace(" ",""), path)
                    files = fileManager.findFiles(dataSource, name.text, path)

            if el.tag == "app":

                try:
                    f = getattr(appfun, el.find("name").text)
                except:
                    self.log(Level.INFO, "Error to load the function "+el.find("name").text)
                else:
                    #files = fileManager.findFiles(dataSource, el.find("filename").text, el.find("path").text)
                    files = fileManager.findFiles(dataSource, el.find("filename").text, el.find("path").text)
                    if files:
                        data = f(files)
                        #self.log(Level.INFO, "Ha trovato file e data = "+str(data))

                finally:
                    files = []



            for file in files:
                self.log(Level.INFO, "Processing file: " + file.getName())
                elCount += 1



                # Handles the file
                handler = FileHandler(file, file.getNameExtension(), file.getName(), file.getUniquePath())

                if handler.store_file(Case.getCurrentCase().getTempDirectory()):

                    if el.tag == "pic" and handler.isPic():
                        self.log(Level.INFO, "Element pic, guardo file")

                        res = handler.processPic()
                        if res:
                            res["name"] = handler.getName()
                            res["type"] = "pic"
                            data.append({"file":file,"el":[res]})
                            self.log(Level.INFO, "dati trovati el = "+str([res]))

                    if el.tag == "db":
                        self.log(Level.INFO, "Element db, guardo file")

                        if handler.connect():
                            self.log(Level.INFO, "Okay db")
                            tables_tag = el.find("tables")

                            tables = handler.getTables() if not tables_tag else tables_tag

                            fileobj = { "file":file, "el":[]}

                            for table in tables:



                                if not tables_tag:
                                    resultSet = handler.query(table)
                                    tablename = table
                                    try:
                                        resultSetMetaData = resultSet.getMetaData()
                                        numColumns = resultSetMetaData.getColumnCount()
                                    except:
                                        resultSetMetaData = None
                                        numColumns = None
                                else:
                                    tablename = table.attrib["name"]
                                    resultSet = handler.query(table.attrib["name"])
                                    resultSetMetaData = None
                                    numColumns = None

                                if (tables_tag and resultSet) or ( not tables_tag and (resultSet and resultSetMetaData and numColumns)):
                                    rows = []
                                    while resultSet.next():
                                        attributes = {}

                                        columns = range(1, numColumns + 1 ) if not tables_tag else table.findall("column")


                                        for column in columns:

                                            if not tables_tag:
                                                try:
                                                    nameColumn = resultSetMetaData.getColumnName(column)
                                                except:
                                                    nameColumn = None
                                            else:

                                                if column.get("type") == "linked_datetime":
                                                    # TODO: put controls
                                                    res=handler.query(column.get("table"))
                                                    while res.next():
                                                        value = res.getString(column.text)
                                                        attributes["datetime"] = long(value)
                                                        attributes["column_datetime"] = column.text
                                                    nameColumn = None
                                                else:
                                                    nameColumn = column = column.text

                                            if nameColumn:
                                                temp = handler.processDB(resultSet, column, nameColumn, self.dict)
                                                if temp:
                                                    if temp[0] == "single":
                                                        attributes[temp[1]] = temp[2]
                                                        attributes["name"] = handler.getName()
                                                        attributes["type"] = "db"
                                                        attributes["table"] = tablename
                                                        attributes["path"] = handler.getPath()
                                                        if temp[1] in ("latitude", "longitude", "datetime", "text"):
                                                            attributes["column_"+temp[1]] = nameColumn

                                                    if temp[0] == "multiple":
                                                        if temp[1]:
                                                            for x in temp[1]:
                                                                x["name"] = handler.getName()
                                                                x["table"] = tablename
                                                                x["type"] = "db"
                                                                x["path"] = handler.getPath()
                                                                x["column"] = nameColumn
                                                            rows = rows + temp[1]


                                        if attributes: rows.append(attributes)

                                    if rows: fileobj["el"] = fileobj["el"] + rows

                            data.append(fileobj)

                            handler.close()

            if data:
                self.log(Level.INFO, "Final data = "+str(data))

                for f in data:
                    file = f["file"]
                    for item in f["el"]:
                        self.log(Level.INFO, "check el = "+str(item))
                        if "latitude" and "longitude" in item:
                            art = file.newArtifact(BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACKPOINT)

                            if "datetime" in item:
                                if item["datetime"] != "":
                                    if isinstance(item["datetime"],str):
                                        if el.tag == "pic":
                                            att3 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DATETIME.getTypeID(),
                                                                       AndroidGeodataXMLFactory.moduleName, timestamp.getTimestampFromPicDatetime(item["datetime"]) )
                                        else:
                                            att3 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DATETIME.getTypeID(),
                                                                       AndroidGeodataXMLFactory.moduleName, timestamp.getTimestampFromString(item["datetime"]) )
                                    else:
                                        att3 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DATETIME.getTypeID(),
                                                                   AndroidGeodataXMLFactory.moduleName,  timestamp.epochTOtimestamp(item["datetime"]))

                                    art.addAttribute(att3)

                            att1 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_GEO_LATITUDE.getTypeID(),
                                                       AndroidGeodataXMLFactory.moduleName, item["latitude"])

                            att2 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_GEO_LONGITUDE.getTypeID(),
                                                       AndroidGeodataXMLFactory.moduleName, item["longitude"])

                            att4 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_PROG_NAME.getTypeID(),
                                                       AndroidGeodataXMLFactory.moduleName, item["name"])

                            art.addAttributes([att1, att2, att4])

                            if "column" in item:
                                att5 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DESCRIPTION.getTypeID(),
                                                           AndroidGeodataXMLFactory.moduleName, "table: "+item["table"]+", column = "+item["column"])
                                art.addAttribute(att5)
                            elif "table" in item:
                                att5 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DESCRIPTION.getTypeID(),
                                                           AndroidGeodataXMLFactory.moduleName, "table: "+item["table"]+", column = "+item["column_latitude"]+", "+item["column_longitude"])
                                art.addAttribute(att5)

                            try:
                                # index the artifact for keyword search
                                blackboard.indexArtifact(art)
                            except Blackboard.BlackboardException as e:
                                self.log(Level.SEVERE, "Error indexing artifact " + art.getDisplayName())



                        elif "text" in item:

                            art_text = file.newArtifact(blackboard.getOrAddArtifactType("geodataTEXT","Geodata in text").getTypeID())
                            att = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_TEXT.getTypeID(),
                                                      AndroidGeodataXMLFactory.moduleName, item["text"] )
                            if "column_text" and "table" in item:
                                att1 = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_DESCRIPTION.getTypeID(),
                                                           AndroidGeodataXMLFactory.moduleName, "table: "+item["table"]+", column = "+item["column_text"])

                            art_text.addAttributes([att,att1])

                            try:
                                # index the artifact for keyword search
                                blackboard.indexArtifact(art_text)
                            except Blackboard.BlackboardException as e:
                                self.log(Level.SEVERE, "Error indexing artifact " + art_text.getDisplayName())




        # TODO: put it at the end to avoid a lot of notification, understand the artifact type
        # Fire an event to notify the UI and others that there are new artifacts
        IngestServices.getInstance().fireModuleDataEvent(
            ModuleDataEvent(AndroidGeodataXMLFactory.moduleName,
                BlackboardArtifact.ARTIFACT_TYPE.TSK_INTERESTING_ARTIFACT_HIT, None))

        # After all databases, post a message to the ingest messages in box.
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
                                                                                                "AndroidGeodataXML", "no errors")
        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK
