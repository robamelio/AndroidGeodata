"""
AndroidGeodataCrawler is part of the AndroidGeodata project,
see the project page for more information https://github.com/robiame/AndroidGeodata.

AndroidGeodataCrawler is the File Ingest Module that thoroughly scans an Android
dump looking for elements (DBs, pics, etc.), which may contain geodata, and displaying
them on the Autopsy blackboard creating an XML report compatible with AndroidGeodataXML.


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
from dbvalue.util import util

import inspect
import json
import os
import xml.dom.minidom
import xml.etree.cElementTree as et

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

from java.lang import IllegalArgumentException
from org.sleuthkit.autopsy.ingest import IngestModuleIngestJobSettings
from org.sleuthkit.autopsy.ingest import IngestModuleIngestJobSettingsPanel
from org.sleuthkit.autopsy.ingest import IngestModuleGlobalSettingsPanel
from javax.swing import JCheckBox
from javax.swing import BoxLayout

#######################################
# Autopsy File Ingest Module Template #
#######################################

# Factory that defines the name and details of the module and allows Autopsy
# to create instances of the modules that will do the anlaysis.
class AndroidGeodataCrawlerFactory(IngestModuleFactoryAdapter):
    def __init__(self):
        self.settings = None

    moduleName = "Android Geodata Crawler"

    def getModuleDisplayName(self):
        return self.moduleName

    def getModuleDescription(self):
        return ""

    def getModuleVersionNumber(self):
        return "1.0"

    ########## UI ###########
    def getDefaultIngestJobSettings(self):
        return UISettings()

    # Keep enabled only if you need ingest job-specific settings UI
    def hasIngestJobSettingsPanel(self):
        return True

    # TODO: Update class names to ones that you create below
    def getIngestJobSettingsPanel(self, settings):
        if not isinstance(settings, UISettings):
            raise IllegalArgumentException("Expected settings argument to be instance of UISettings")
        self.settings = settings
        return UISettingsPanel(self.settings)
    ############ UI ##########

    # Return true if module wants to get called for each file
    def isFileIngestModuleFactory(self):
        return True

    # can return null if isFileIngestModuleFactory returns false
    def createFileIngestModule(self, ingestOptions):
        return AndroidGeodataCrawler(self.settings)


# File-level ingest module.  One gets created per thread.
class AndroidGeodataCrawler(FileIngestModule):

    _logger = Logger.getLogger(AndroidGeodataCrawlerFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    # Autopsy will pass in the settings from the UI panel
    def __init__(self, settings):
        self.local_settings = settings

    # Where any setup and configuration is done
    # 'context' is an instance of org.sleuthkit.autopsy.ingest.IngestJobContext.
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_ingest_job_context.html
    def startUp(self, context):
        # Determine if user configured a flag in UI
        if self.local_settings.getFlag():
            self.stanpl = True
        else:
            self.stanpl = False

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
            try:
                self.dict = json.load( open(path_to_dict) )
            except:
                raise IngestModuleException("The dictionary file was not loaded")

    # Where the analysis is done.  Each file will be passed into here.
    # The 'file' object being passed in is of type org.sleuthkit.datamodel.AbstractFile.
    def process(self, file):

        ####################
        # Proprietary code #
        ####################

        # Functions
        def getBlackboardAtt(label, value):
            return BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.fromLabel(label).getTypeID(),
                                       AndroidGeodataCrawlerFactory.moduleName, value )

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

        # Analyse only the files:
        if ext in ("", "db", "pic", "json", "txt", "log"):
            # Handles the file
            handler = FileHandler(file, file.getNameExtension(), file.getName(), file.getUniquePath(), file.getId(), self.stanpl )

            # Stores the file
            if handler.store_file(Case.getCurrentCase().getTempDirectory()):
                # Bool value to check whether the file has been analysed to stop other controls
                bool = True

                # # # # # # # # # # # # # # # # # # # # # # # # # # #  #
                #                                                      #
                # At the moment supported files are: db, pic and json. #
                #                                                      #
                # # # # # # # # # # # # # # # # # # # # # # # # # # #  #

                # If db
                if ext in ("db",""):

                    self.dbFound += 1

                    if ext == "db":
                        bool = False

                    # Tries a connection to verify whether the file is a db
                    if handler.connect() and not (util.findValue( handler.getName(), self.dict, "dict_db")):
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

                                if (resultSet and resultSetMetaData and numColumns):
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
                                                            if not "column_other" in attributes:
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

                                        if attributes:
                                            rows.append(attributes)

                                    if rows:
                                        data = data + rows

                            handler.close()

                # the file is not a db, is it a pic then?
                if ext in ("pic", "") and bool:
                    self.picFound += 1

                    if ext == "pic":
                        bool = False

                    res = handler.processPic()
                    if res:
                        bool = False
                        res["name"] = handler.getName()
                        res["path"] = handler.getPath()
                        res["type"] = "pic"
                        res["description"] = "from pic"
                        data.append(res)

                # The file is not a pic either, is it a file json?
                if ext in ("json","") and bool:
                    self.jsonFound += 1

                    if ext == "json":
                        bool = False

                    res = handler.processJsonFile()
                    if res:
                        bool = False
                        for x in res:
                            x["name"] = handler.getName()
                            x["path"] = handler.getPath()
                            x["type"] = "json"
                            x["description"] = "from file json"

                        data += res

                if bool and self.stanpl:
                    res = handler.processFile()
                    if res:
                        res["name"] = handler.getName()
                        res["path"] = handler.getPath()
                        res["type"] = "file"
                        res["description"] = "from file"

                        data.append(res)

                # Deletes the file temporarily stored
                e = handler.delete_file()
                if e:
                    self.log(Level.INFO, "Error in deleting the file "+handler.getName()+", message = "+e)

        if data:
            el = None
            el_rep = None
            for item in data:
                if "latitude" and "longitude" in item:

                    if not el:
                        # No element
                        el = et.SubElement(self.root, item["type"])
                        et.SubElement(el, "app").text = item["path"]
                        et.SubElement(el, "path").text = item["path"]
                        et.SubElement(el, "name").text = item["name"]
                        if "table" in item:
                            tables = et.SubElement(el, "tables")
                            table = et.SubElement(tables, "table", name=item["table"])
                            if "column" in item:
                                et.SubElement(table,"column", type="json").text = item["column"]
                            else:
                                et.SubElement(table,"column", type="latitude").text = item["column_latitude"]
                                et.SubElement(table,"column", type="longitude").text = item["column_longitude"]
                                if "column_datetime" in item:
                                    et.SubElement(table,"column", type="datetime").text = item["column_datetime"]
                    else:
                        #Element already exists
                        if not any(table.get("name") == item["table"] for table in el.find("tables").iter("table") ):
                            #No table
                            table = et.SubElement(el.find("tables"), "table", name=item["table"])
                            if "column" in item:
                                et.SubElement(table,"column", type="json").text = item["column"]
                            else:
                                et.SubElement(table,"column", type="latitude").text = item["column_latitude"]
                                et.SubElement(table,"column", type="longitude").text = item["column_longitude"]
                                if "column_datetime" in item:
                                    et.SubElement(table,"column", type="datetime").text = item["column_datetime"]

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

                if "text" in item:
                    if not el:
                        # No element
                        el = et.SubElement(self.root, item["type"])
                        et.SubElement(el, "app").text = item["path"] #.split("\/")[-2]
                        et.SubElement(el, "path").text = item["path"]
                        et.SubElement(el, "name").text = item["name"]
                        if "table" in item:
                            tables = et.SubElement(el, "tables")
                            table = et.SubElement(tables, "table", name=item["table"])
                            if "column_text" in item:
                                et.SubElement(table,"column", type="text").text = item["column_text"]
                    else:
                        #Element already exists
                        if not any(table.get("name") == item["table"] for table in el.find("tables").iter("table") ):
                            #No table
                            table = et.SubElement(el.find("tables"), "table", name=item["table"])
                            if "column_text" in item:
                                et.SubElement(table,"column", type="text").text = item["column_text"]


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

                if "column_other" in item:
                    if not el_rep:
                        # No element
                        el_rep = et.SubElement(self.root_report, item["type"])
                        et.SubElement(el_rep, "app").text = item["path"]
                        et.SubElement(el_rep, "path").text = item["path"]
                        et.SubElement(el_rep, "name").text = item["name"]
                        tables = et.SubElement(el_rep, "tables")
                        table = et.SubElement(tables, "table", name=item["table"])
                        for column in item["column_other"]:
                            et.SubElement(table,"column", type="").text = column
                    else:
                        # Element already exists
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

    # Where any shutdown code is run and resources are freed.
    # TODO: Add any shutdown code that you need here.
    def shutDown(self):
        self.xmlname += "_"+str(self.picFound)+str(self.dbFound)+str(self.jsonFound)+str(self.filesFound)+"_androidgeodata.xml"

        report = open(self.xmlname, 'w')
        report.write(
            str(xml.dom.minidom.parseString(et.tostring(self.root)).toprettyxml())+
            " \n <!-- Report of possible other coordinates --> \n <!--"+
            str(xml.dom.minidom.parseString(et.tostring(self.root_report)).toprettyxml())
            +"-->" )
        report.close()
        Case.getCurrentCase().addReport(self.xmlname, AndroidGeodataCrawlerFactory.moduleName, "AndroidGeodata XML")
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA, AndroidGeodataCrawlerFactory.moduleName,
             "In this thread: "+
            str(self.filesFound)+" files found, "+
            str(self.picFound)+" pictures, "+
            str(self.dbFound)+" DBs and "+
            str(self.jsonFound)+" json processed. "
            "\n A xml ("+self.xmlname+") and a report have been created ")
        IngestServices.getInstance().postMessage(message)
        
    
########################### UI #############################################
# Stores the settings that can be changed for each ingest job
# All fields in here must be serializable.  It will be written to disk.
class UISettings(IngestModuleIngestJobSettings):
    serialVersionUID = 1L

    def __init__(self):
        self.flag = False

    def getVersionNumber(self):
        return serialVersionUID

    # Define getters and settings for data you want to store from UI
    def getFlag(self):
        return self.flag

    def setFlag(self, flag):
        self.flag = flag


# UI that is shown to user for each ingest job so they can configure the job.
class UISettingsPanel(IngestModuleIngestJobSettingsPanel):
    # Note, we can't use a self.settings instance variable.
    # Rather, self.local_settings is used.
    # https://wiki.python.org/jython/UserGuide#javabean-properties
    # Jython Introspector generates a property - 'settings' on the basis
    # of getSettings() defined in this class. Since only getter function
    # is present, it creates a read-only 'settings' property. This auto-
    # generated read-only property overshadows the instance-variable -
    # 'settings'

    # We get passed in a previous version of the settings so that we can
    # prepopulate the UI
    # TODO: Update this for your UI
    def __init__(self, settings):
        self.local_settings = settings
        self.initComponents()
        self.customizeComponents()

    # TODO: Update this for your UI
    def checkBoxEvent(self, event):
        if self.checkbox.isSelected():
            self.local_settings.setFlag(True)
        else:
            self.local_settings.setFlag(False)

    # TODO: Update this for your UI
    def initComponents(self):
        self.setLayout(BoxLayout(self, BoxLayout.Y_AXIS))
        self.checkbox = JCheckBox("Stanford CoreNLP", actionPerformed=self.checkBoxEvent)
        self.add(self.checkbox)

    # TODO: Update this for your UI
    def customizeComponents(self):
        self.checkbox.setSelected(self.local_settings.getFlag())

    # Return the settings used
    def getSettings(self):
        return self.local_settings