import sys

from enum import Enum
from tracerecord import TraceRecord
from traceprocessor import *
from tracethread import *
from threadpool import *
from tracesocket import *
from socketpool import *

traceProcessor = TraceProcessor(pathToPIDListFile=sys.argv[1],
                                gatewayIP=sys.argv[2])


# pass input of report (raw format) through "sed -E 's/,\s*/,/g'""
# Create threads which exist upon container startup

for line in sys.stdin:
    record = TraceRecord(line)
    traceProcessor.consumeRecord(record)
    # print(record.pid, record.cpu, record.timeStamp, record.event, record.details)
