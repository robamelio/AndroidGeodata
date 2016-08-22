import datetime
import time

class timestamp():

    @staticmethod
    def getTimestampFromString(value):

        d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')

        return int(time.mktime(d.timetuple()))

    @staticmethod
    def getTimestampFromPicDatetime(value):

        date = value.split(" ")[0].split(":")

        time_var = value.split(" ")[1].split(":")

        d = datetime.datetime(year=int(date[0]),month=int(date[1]),day=int(date[2]),hour=int(time_var[0]),minute=int(time_var[1]),second=int(time_var[2]))

        return int(time.mktime(d.timetuple()))

    @staticmethod
    def epochTOtimestamp(value):
        return int(time.mktime(time.gmtime(value/1000.)))