from enum import Enum
from tracerecord import TraceRecord
import sys
from THREAD import *

DEBUG = 0


class SocketElement():

    def __init__(self, socketCookie: int, srcIP: str, destIP: str, srcPort: int, destPort: int):
        self.socketCookie = socketCookie
        self.srcIP = srcIP
        self.destIP = destIP
        self.srcPort = srcPort
        self.destPort = destPort
        self.srcThread = None
        self.destThread = None

    def updateSrcThread(self, srcThread: Thread):
        self.srcThread = srcThread

    def updateDestThread(self, destThread: Thread):
        self.destThread = destThread

# class RootEvents():





class ThreadPool():

    def __init__(self):
        self.ActiveThreadPool = dict()  # key is PID, value is a Thread object
        self.DeadThreadPool = list()  # contains Dead Thread objects

    def freeActiveThreadPool(self):
        for key in list(self.ActiveThreadPool.keys()):
            self.DeadThreadPool.append(self.ActiveThreadPool.pop(key))

    def addThread(self, newThread: Thread):
        if newThread.pid not in self.ActiveThreadPool:
            self.ActiveThreadPool[newThread.pid] = newThread
            return True
        return False

    def killThread(self, killThread: Thread):
        if killThread.pid in self.ActiveThreadPool:
            self.DeadThreadPool.append(
                self.ActiveThreadPool.pop(killThread.pid))
            return True
        return False

    def killPid(self, killPid: int):
        if killPid in self.ActiveThreadPool:
            self.DeadThreadPool.append(self.ActiveThreadPool.pop(killPid))
            return True
        return False

# pass input of report (raw format) through "sed -E 's/,\s*/,/g'""

# Create threads which exist upon container startup
threadPool = ThreadPool()
with open("traceData/pids.txt", "r") as initialThreads:
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
