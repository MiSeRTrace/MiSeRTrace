import sys

from enum import Enum
from tracerecord import TraceRecord
from traceprocessor import *
from tracethread import *
from threadpool import *
from tracesocket import *
from socketpool import *

traceProcessor = TraceProcessor(pathToPIDListFile=sys.argv[1], gatewayIP=sys.argv[2])

printLines = "-l" in sys.argv
lineNumber = 1

for line in sys.stdin:
    if printLines:
        print(lineNumber, end="")
        lineNumber += 1
    record = TraceRecord(line)
    if not traceProcessor.consumeRecord(record):
        print("Record Validation Failed")
        exit()
    if printLines:
        print("\n--------\n")
