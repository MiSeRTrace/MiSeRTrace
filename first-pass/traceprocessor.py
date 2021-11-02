from socketpool import *
from threadpool import *
from tracerecord import *
from globalstatemanager import GlobalStateManager


class TraceProcessor():
    def __init__(self, pathToPIDListFile: str, gatewayIP: str):
        self.threadPool: ThreadPool = ThreadPool()
        self.socketPool: SocketPool = SocketPool()
        self.gatewayIP = gatewayIP
        # self.globalStateManager: GlobalStateManager = GlobalStateManager(
        #     gsClasses=gsClasses)
        with open(pathToPIDListFile, "r") as initialThreads:
            for line in initialThreads.readlines():
                pid, container, _ = line.strip().split()
                pid = int(pid)
                self.threadPool.addThread(
                    Thread(pid, container, self.threadPool, self.socketPool))

    def consumeRecord(self, record: TraceRecord):
        if not self._validRecord(record):
            return False
        self.threadPool.processSched(record)
        self.processThread(record)
        return True

    # basic validation checks can be added here
    def _validRecord(self, record: TraceRecord):
        return True

    def processThread(self, record: TraceRecord):
        thread: Thread = self.threadPool.getThread(record.pid)
        if thread:
            thread.consumeRecord(record)
