import sys

from enum import Enum
from tracerecord import TraceRecord
from traceprocessor import *
from tracethread import *
from threadpool import *
from tracesocket import *
from socketpool import *

sys.setrecursionlimit(10000)
traceProcessor = TraceProcessor(inputFilePath=sys.argv[1], gatewayIP=sys.argv[2])

printLines = "-l" in sys.argv
lineNumber = 1


verbose = "-v" in sys.argv
if verbose:
    traceProcessor.toPrint = True
else:
    traceProcessor.toPrint = False

rawFormat = "-R" in sys.argv
if rawFormat:
    traceProcessor.rawFormat = True
else:
    traceProcessor.rawFormat = False

colored = "-c" in sys.argv
if colored:
    traceProcessor.colored = True
else:
    traceProcessor.colored = False

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

traceProcessor.terminate()
print("Estimated number of requests: ", len(traceProcessor.traceGenesis))

traceProcessor.serializeTraceData()
