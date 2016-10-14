# Android Geodata

This project contains two Python modules for [Autopsy](http://www.autopsy.com/), a digital forensics platform.

The modules aim to collect and display significant amounts of data through which an investigator can consider reporting whereabouts the analysed Android device has been taken. 

# Table of contents

* [Description](README.md#Description)
* [XML](README.md#XML)
* [Dictionary](README.md#Dictionary)
* [Installation](README.md#Installation)
* [Usage](README.md#Usage)
* [License](README.md#License)

# Description

The module Android Geodata Crawler is a File Ingest Module that scans all the files inside a data source and generates an XML file  as a final report.

The module Android Geodata XML is a Data Source Ingest Module that extracts information from a data source considering an XML file, which represents the elements to extract, given as input. 

The modules look for GPS coordinates or words related to locations, which are shown under the labels 'GPS Trackpoints' and 'Geodata in text' respectively. 

# XML

An XML file is used to describe files containing geodata. Below it is shown a simple version of a valid XML file, which contains an example for every element supported so far. 


Firstly, the root element in the XML has to be _androidgeodata_ and, in general, in every element there is the subelement _app_ which is not compulsory as the software does not parse it, it is only needed to add information about the application.

The _pic_ element is used to collect information from pictures. It requires only the subelement _path_ that specifies the path to the directory where the software has to look for pictures.

The _db_ element defines a database containing geodata. It requires the subelements _path_ and _name_, the latter specifies the name of the database situated in the indicated path. Knowing that some applications store the same database with a different name in various phones, it is possible to avoid to specify a complete name by using the character _%_. An example of this is the _db_ element for Twitter, which names databases using different prefixes for each phone, therefore, it is possible to find the database setting as a name to look for the value _%-46.db_. Also, it is possible specifying the subelement _tables_ which can contain one or more subelements _table_. The latter is used to define the table and the columns contained in the database where information is collected. The element _table_ required the attribute _name_ to specify the name of the table and one or more subelements _column_. This subelement needs the attribute _type_ to specify which type of data does the column contain. The supported values are: latitude, longitude, datetime, JSON, text and linked_datetime. The latter is used to state that the _datetime_ value is retrievable from the table specified as attribute _table_ (This case is shown in the _db_ element defined for the Foursquare application). In general, a _column_ element contains text representing the name of the column. If the element _tables_ is not declared, the software looks for geodata in all the tables inside the database.

The element _file_ and _json_ are used to collect information from JSON files and from files that are not either DB, pictures or JSON. They required the subelements _path_ and _name_. 

Finally, the element _app_ is used to declare customised functions to examine specific applications. It needs the subelement _name_ that represents the name of the function the software has to call, _path_ that is the path of the directory and _filename_ that defines the name of the file to elaborate. If the latter is not included, the software works on every file in the directory.

# Dictionary

# Installation

# Usage

# License

This project is under the MIT License.

See the file [LICENSE](LICENSE).
