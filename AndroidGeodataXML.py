"""
AndroidGeodataXML is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

AndroidGeodataXML is the Data Source Ingest Module that receives an XML file,
which represents elements (DBs, pics, etc..) that contain geodata, and displays
the geodata found on the Autopsy blackboard.


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
from dbvalue.timestamp import timestamp
from appfun import appfun

import inspect
import os
import xml.etree.cElementTree as et
import json

from java.util.logging import Level
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
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

##############################################
# Autopsy Data Source Ingest Module Template #
##############################################

# Factory that defines the name and details of the module and allows Autopsy
# to create instances of the modules that will do the analysis.
class AndroidGeodataXMLFactory(IngestModuleFactoryAdapter):
    moduleName = "Android Geodata XML"

    def getModuleDisplayName(self):
        return self.moduleName

    # TODO: Give it a description
    def getModuleDescription(self):
        return ""

    def getModuleVersionNumber(self):
        return "1.0"

    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingestOptions):
        return AndroidGeodataXML()


# Data Source-level ingest module.  One gets created per data source.
class AndroidGeodataXML(DataSourceIngestModule):
    _logger = Logger.getLogger(AndroidGeodataXMLFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def __init__(self):
        self.context = None

    # Where any setup and configuration is done
    # 'context' is an instance of org.sleuthkit.autopsy.ingest.IngestJobContext.
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_ingest_job_context.html
    def startUp(self, context):
        self.context = context

        # Verification of the xml
        path_to_xml = os.path.dirname(os.path.abspath(__file__)) + '/geodata.xml'
        if not os.path.exists(path_to_xml):
            raise IngestModuleException("The xml file was not found in module folder")
        else:
            self.data_from_xml = open(path_to_xml).read()

        # Verification of the JSON
        path_to_dict = os.path.dirname(os.path.abspath(__file__)) + '/dictionary.json'
        if not os.path.exists(path_to_dict):
            raise IngestModuleException("The dictionary file was not found in module folder")
        else:
            try:
                self.dict = json.load( open(path_to_dict) )
            except:
                raise IngestModuleException("The dictionary file was not loaded")

    # Where the analysis is done.
    # The 'dataSource' object being passed in is of type org.sleuthkit.datamodel.Content.
    # See: http://www.sleuthkit.org/sleuthkit/docs/jni-docs/4.3/interfaceorg_1_1sleuthkit_1_1datamodel_1_1_content.html
    # 'progressBar' is of type org.sleuthkit.autopsy.ingest.DataSourceIngestModuleProgress
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_data_source_ingest_module_progress.html
    def process(self, dataSource, progressBar):

        ####################
        # Proprietary code #
        ####################

        # Functions
        def getBlackboardAtt(label, value):
            return BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.fromLabel(label).getTypeID(),
                                       AndroidGeodataXMLFactory.moduleName, value )

        def cleanString(s):
            s = s.replace("\n","").replace("\t","")
            while s.startswith(" "):
                s = s[1:]
            while s.endswith(" "):
                s = s[:len(s)-1]
            return s

        # we don't know how much work there is yet
        progressBar.switchToIndeterminate()

        # Use blackboard class to index blackboard artifacts for keyword search
        blackboard = Case.getCurrentCase().getServices().getBlackboard()

        # FileManager for the current case
        fileManager = Case.getCurrentCase().getServices().getFileManager()

        # object to represent the XML
        tree = et.fromstring(self.data_from_xml)
        numEl = len(tree)
        progressBar.switchToDeterminate(numEl)
        fileCount = 0
        elCount = 0

        # TODO: remove blank spaces
        for el in tree:

            # Check if the user pressed cancel while we were busy
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK

            # Counts element
            elCount += 1

            # Inits variables
            data = []
            files = []

            path = el.find("path")
            if path is not None:
                path = cleanString(path.text)

            name = el.find("name")
            if name is not None:
                name = cleanString(name.text)

            # If the current element is pic
            if el.tag == "pic" and path:
                files = fileManager.findFiles(dataSource, "%", path)

            # If the current element is db
            if el.tag == "db" and path:
                files = fileManager.findFiles(dataSource, "%", path) if name is None\
                    else fileManager.findFiles(dataSource, name, path)

            # If the current element is either file or json
            if el.tag in ("file","json") and path:
                files = fileManager.findFiles(dataSource, name, path) if name is not None else []

            # If the current element is app
            if el.tag == "app" and name and path:
                try:
                    f = getattr(appfun, name)
                except:
                    self.log(Level.INFO, "Error to load the function "+name)
                else:
                    filename = el.find("filename")
                    if filename is not None:
                        filename = cleanString(filename.text)
                        files = fileManager.findFiles(dataSource, filename, path)
                        if files:
                            data = f(files)
                finally:
                    files = []

            # Files contain all the files found and file would be each one of them per cycle
            for file in files:
                fileCount += 1

                # Handles the file
                handler = FileHandler(file, file.getNameExtension(), file.getName(), file.getUniquePath(), file.getId())

                if handler.store_file(Case.getCurrentCase().getTempDirectory()):

                    if el.tag == "pic" and handler.isPic():
                        res = handler.processPic()
                        if res:
                            res["name"] = handler.getName()
                            res["type"] = "pic"
                            res["description"] = "from pic"
                            data.append({"file":file,"el":[res]})

                    if el.tag == "db":
                        if handler.connect():
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
                                                    res = handler.query(cleanString(column.get("table")))
                                                    while res.next():
                                                        try:
                                                            value = res.getString(cleanString(column.text))
                                                        except:
                                                            pass
                                                        else:
                                                            attributes["datetime"] = long(value)
                                                            attributes["column_datetime"] = cleanString(column.text)
                                                    nameColumn = None
                                                else:
                                                    nameColumn = column = cleanString(column.text)

                                            if nameColumn:
                                                temp = handler.processDB(resultSet, column, nameColumn, self.dict, False)
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

                                        if attributes:
                                            rows.append(attributes)

                                    if rows:
                                        fileobj["el"] = fileobj["el"] + rows

                            data.append(fileobj)

                            handler.close()

                    if el.tag == "json":
                        res = handler.processJsonFile()
                        if res:
                            for x in res:
                                x["name"] = handler.getName()
                                x["path"] = handler.getPath()
                                x["type"] = "json"
                                x["description"] = "from file json"
                            data.append({"file":file,"el":res})

                    if el.tag == "file":
                        res = {}
                        res["name"] = handler.getName()
                        res["path"] = handler.getPath()
                        res["type"] = "file"
                        res["text"] = "look at the file"
                        res["description"] = "from file"
                        data.append({"file":file,"el":[res]})

                    if not handler.delete_file():
                        self.log(Level.INFO, "Error in deleting the file "+handler.getlclPath())

            # Display the results
            if data:
                for f in data:
                    file = f["file"]
                    for item in f["el"]:

                        if "latitude" and "longitude" in item:
                            art = file.newArtifact(BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACKPOINT)

                            if "datetime" in item and item["datetime"] != "":
                                if isinstance(item["datetime"],str):
                                    if el.tag == "pic":
                                        att1 = getBlackboardAtt("TSK_DATETIME", timestamp.getTimestampFromPicDatetime(item["datetime"]))
                                    else:
                                        att1 = getBlackboardAtt("TSK_DATETIME", timestamp.getTimestampFromString(item["datetime"]))
                                else:
                                    if len(str(item["datetime"])) == 10:
                                        att1 = getBlackboardAtt("TSK_DATETIME",  item["datetime"])
                                    elif len(str(item["datetime"])) == 13:
                                        att1 = getBlackboardAtt("TSK_DATETIME",  int(item["datetime"]/1000))
                                art.addAttribute(att1)

                            att2 = getBlackboardAtt("TSK_GEO_LATITUDE", item["latitude"])

                            att3 = getBlackboardAtt("TSK_GEO_LONGITUDE", item["longitude"])

                            att4 = getBlackboardAtt("TSK_PROG_NAME", item["name"])

                            art.addAttributes([att2, att3, att4])

                            if "column" in item:
                                att5 = getBlackboardAtt("TSK_DESCRIPTION", "table: "+item["table"]+", column = "+item["column"])
                                art.addAttribute(att5)
                            elif "table" in item:
                                att5 = getBlackboardAtt("TSK_DESCRIPTION", "table: "+item["table"]+", column = "+item["column_latitude"]+", "+item["column_longitude"])
                                art.addAttribute(att5)
                            elif "description" in item:
                                att5 = getBlackboardAtt("TSK_DESCRIPTION", item["description"])
                                art.addAttribute(att5)

                            try:
                                # index the artifact for keyword search
                                blackboard.indexArtifact(art)
                            except Blackboard.BlackboardException:
                                self.log(Level.SEVERE, "Error indexing artifact " + art.getDisplayName())


                        elif "text" in item:

                            art_text = file.newArtifact(blackboard.getOrAddArtifactType("geodataTEXT","Geodata in text").getTypeID())
                            att = getBlackboardAtt("TSK_TEXT", item["text"] )
                            art_text.addAttribute(att)
                            if "column_text" and "table" in item:
                                att1 = getBlackboardAtt("TSK_DESCRIPTION", "table: "+item["table"]+", column = "+item["column_text"])
                                art_text.addAttribute(att1)
                            elif "description" in item:
                                att1 = getBlackboardAtt("TSK_DESCRIPTION", item["description"])
                                art_text.addAttribute(att1)

                            try:
                                # index the artifact for keyword search
                                blackboard.indexArtifact(art_text)
                            except Blackboard.BlackboardException:
                                self.log(Level.SEVERE, "Error indexing artifact " + art_text.getDisplayName())

            # Update the progress bar
            progressBar.progress(elCount)

        # Fire an event to notify the UI and others that there are new artifacts
        IngestServices.getInstance().fireModuleDataEvent(
            ModuleDataEvent(AndroidGeodataXMLFactory.moduleName,
                BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACKPOINT, None))

        # After all databases, post a message to the ingest messages in box.
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
               "AndroidGeodataXML", str(elCount)+" elements in the XML and "+str(fileCount)+" files processed")
        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK
