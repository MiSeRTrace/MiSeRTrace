import sys

from enum import Enum
from tracerecord import TraceRecord
from traceprocessor import *
from tracethread import *
from tracethreadpool import *
from tracesocket import *
from tracesocketpool import *

DEBUG = 0

# class RootEvents():


traceProcessor = TraceProcessor()

# Function assumed format as PID, container, container id
# Output is of command ________ #TODO
traceProcessor.initializeThreadPool("first-pass/traceData/pids.txt")

# pass input of report (raw format) through "sed -E 's/,\s*/,/g'""
# Create threads which exist upon container startup
for line in sys.stdin:
    record = TraceRecord(line)
    traceProcessor.consumeRecord(record)
    print(record.pid, record.cpu, record.timeStamp, record.event, record.details)
