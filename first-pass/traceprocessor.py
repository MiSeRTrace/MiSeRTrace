from tracesocketpool import *
from tracethreadpool import *
from tracerecord import *
from globalstatemanager import GlobalStateManager


class TraceProcessor():

    def __init__(self, pathToPIDListFile: str,gatewayIP:str):
        self.threadPool: ThreadPool = ThreadPool()
        self.socketPool: SocketPool = SocketPool()
        # self.globalStateManager: GlobalStateManager = GlobalStateManager(
        #     gsClasses=gsClasses)
        self.previousTimeStamp: float = 0.0
        with open(pathToPIDListFile, "r") as initialThreads:
            for line in initialThreads.readlines():
                pid, container, _ = line.strip().split()
                pid = int(pid)
                self.threadPool.addThread(Thread(pid, container))
        self.gatewayIP=gatewayIP

    # basic validation checks can be added here
    def _validRecord(self, record: TraceRecord):
        # ensures that the records are inserted in non-decreasing order of time
        if self.previousTimeStamp <= record.timeStamp:
            self.previousTimeStamp = record.timeStamp
            return True
        return False

    def processThread(self,record:TraceRecord):
        thread:Thread = self.threadPool.getThread(record.pid)
        if thread:
            thread.consumeRecord(record)

    def consumeRecord(self, record: TraceRecord):
        if not self._validRecord(record):
            return False
        self.threadPool.processSched(record)
        self.processThread(record)

