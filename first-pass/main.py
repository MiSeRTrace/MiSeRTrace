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

# pass input of report (raw format) through "sed -E 's/,\s*/,/g'""
# Create threads which exist upon container startup
threadPool = ThreadPool()
with open("first-pass/traceData/pids.txt", "r") as initialThreads:
    for line in initialThreads.readlines():
        pid, container, _ = line.strip().split()
        pid = int(pid)
        threadPool.addThread(Thread(pid, container))

if (DEBUG == 1):
    for thread in threadPool.ActiveThreadPool.values():
        print(thread)


for line in sys.stdin:
    record = TraceRecord(line)
    print(record.pid, record.cpu, record.timeStamp, record.event, record.details)
