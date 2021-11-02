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

# pass report (raw format -r) through "sed -E 's/,\s*/,/g'""
# [a, b, c] => [a,b,c]

for line in sys.stdin:
    record = TraceRecord(line)
    if not traceProcessor.consumeRecord(record):
        print("Record Validation Failed")
        exit()
