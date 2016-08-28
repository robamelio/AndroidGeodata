"""
AndroidGeodataXML is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

AndroidGeodataXML is the Data Source Ingest Module that receives an XML file,
which represents elements (DBs, pics, etc..) that contain geodata, and displays
the geodata found on the Autopsy blackboard.


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

            # If the current element is pic
            if el.tag == "pic":
                path = el.find("path")
                if path is not None:
                    path = path.text.replace(" ","")
                    files = fileManager.findFiles(dataSource, "%", path)

            # If the current element is db
            if el.tag == "db":
                path = el.find("path")
                if path is not None:
                    path = path.text.replace(" ","")
                    name = el.find("name")
                    files = fileManager.findFiles(dataSource, "%", path) if name is None\
                        else fileManager.findFiles(dataSource, name.text, path)

            # If the current element is app
            if el.tag == "app":
                name = el.find("name")
                if name is not None:
                    try:
                        f = getattr(appfun, name.text)
                    except:
                        self.log(Level.INFO, "Error to load the function "+name.text)
                    else:

                        filename = el.find("filename")
                        path = el.find("path")
                        if ( filename and path ) is not None:

                            files = fileManager.findFiles(dataSource, filename.text, path.text)
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
                                                    res = handler.query(column.get("table"))
                                                    while res.next():
                                                        try:
                                                            value = res.getString(column.text)
                                                        except:
                                                            pass
                                                        else:
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

                                        if attributes:
                                            rows.append(attributes)

                                    if rows:
                                        fileobj["el"] = fileobj["el"] + rows

                            data.append(fileobj)

                            handler.close()

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
                                att1 =  ( getBlackboardAtt("TSK_DATETIME", timestamp.getTimestampFromPicDatetime(item["datetime"]) ) if el.tag == "pic" \
                                            else getBlackboardAtt("TSK_DATETIME", timestamp.getTimestampFromString(item["datetime"]) ) ) \
                                    if isinstance(item["datetime"],str) \
                                        else getBlackboardAtt("TSK_DATETIME",  timestamp.epochTOtimestamp(item["datetime"]))

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

                            try:
                                # index the artifact for keyword search
                                blackboard.indexArtifact(art)
                            except Blackboard.BlackboardException:
                                self.log(Level.SEVERE, "Error indexing artifact " + art.getDisplayName())


                        elif "text" in item:

                            art_text = file.newArtifact(blackboard.getOrAddArtifactType("geodataTEXT","Geodata in text").getTypeID())
                            att = getBlackboardAtt("TSK_TEXT", item["text"] )
                            if "column_text" and "table" in item:
                                att1 = getBlackboardAtt("TSK_DESCRIPTION", "table: "+item["table"]+", column = "+item["column_text"])

                            art_text.addAttributes([att,att1])

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
