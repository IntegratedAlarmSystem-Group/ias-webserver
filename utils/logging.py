import logging
import datetime as dt


class iasFormatter(logging.Formatter):
    """ Formatter for the logs """

    converter = dt.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        """ Formats the time objects """

        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%dT%H:%M:%S")
            s = "%s.%03d" % (t, record.msecs)
        return s
