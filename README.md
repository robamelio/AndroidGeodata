# Android Geodata

This project contains two Python modules for [Autopsy](http://www.autopsy.com/), a digital forensics platform.

The modules aim to collect and display significant amounts of data through which an investigator can consider reporting whereabouts the analysed Android device has been taken. 

# Table of contents

* [Description](README.md#description)
* [XML](README.md#xml)
* [Dictionary](README.md#dictionary)
* [Installation](README.md#installation)
* [Usage](README.md#usage)
* [License](README.md#license)

# Description

The module Android Geodata Crawler is a File Ingest Module that scans all the files inside a data source and generates an XML file  as a final report.

The module Android Geodata XML is a Data Source Ingest Module that extracts information from a data source considering an XML file, which represents the elements to extract, given as input. 

The modules look for GPS coordinates or words related to locations, which are shown under the labels 'GPS Trackpoints' and 'Geodata in text' respectively. 

# XML

An XML file is used to describe files containing geodata. Below it is shown a simple version of a valid XML file, which contains an example for every element supported so far. 

    <androidgeodata>
        <pic>
            <app version="1.0">Camera</app>
            <path>/media/0/DCIM/Camera/</path>
            </pic>
            <db>
                <app>Chrome</app>
                <path>/data/com.android.chrome/app_chrome/Default/</path>
                <name>History</name>
                <tables>
                    <table name="urls">
                        <column type="text">url</column>
                    </table>
                </tables>
            </db>
            <db>
                <app version="">twitter</app>
                <path>/data/com.twitter.android/databases</path>
                <name>%-46.db</name>
                <tables>
                    <table name="search_queries">
                        <column type="longitude">longitude</column>
                        <column type="latitude">latitude</column>
                        <column type="datetime">time</column>
                    </table>

                    <table name="statuses">
                        <column type="latitude">latitude</column>
                        <column type="longitude">longitude</column>
                    </table>
                </tables>
            </db>
            <db>
                <app>Foursquared</app>
                <path>/data/com.joelapenna.foursquared/databases/</path>
                <name>fsq.db</name>
                <tables>
                    <table name="venues">
                        <column type="latitude">loc_lat</column>
                        <column type="longitude">loc_long</column>
                        <column type="linked_datetime" 
                            table="recently_viewed_venue">last_viewed</column>
                    </table>
                </tables>
            </db>
            <db>
                <app version="1.0">Facebook</app>
                <path>/data/com.facebook.katana/databases/</path>
                <name>places.db</name>
                <tables>
                    <table name="places_model">
                        <column type="json">content</column>
                    </table>
                </tables>
            </db>
           <file>
                <app>Outlook</app>
                <path>/data/com.microsoft.office.outlook/app_logs/</path>
                <name>network.log</name>
            </file>
            <app>
                <name>googlemaps</name>
                <path>/data/com.google.android.apps.maps/cache/http</path>
                <filename>%.0</filename>
            </app>
        </androidgeodata>



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
