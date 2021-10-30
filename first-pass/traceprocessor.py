from tracesocketpool import *
from tracethreadpool import *
from tracerecord import *
from globalstatemanager import GlobalStateManager


class TraceProcessor():

    def __init__(self, gsClasses: list):
        self.threadPool: ThreadPool = ThreadPool()
        self.socketPool: SocketPool = SocketPool()
        self.globalStateManager: GlobalStateManager = GlobalStateManager(
            gsClasses=gsClasses)
        self.previousTimeStamp: float = 0.0

    # basic validation checks can be added here
    def _validRecord(self, record: TraceRecord):
        # ensures that the records are inserted in non-decreasing order of time
        if self.previousTimeStamp <= record.timeStamp:
            self.previousTimeStamp = record.timeStamp
            return True
        return False

    def initializeThreadPool(self, pathToPIDListFile: str):
        """
        The ilde PIDs
        """
        with open(pathToPIDListFile, "r") as initialThreads:
            for line in initialThreads.readlines():
                pid, container, _ = line.strip().split()
                pid = int(pid)
                self.threadPool.addThread(Thread(pid, container))

    def consumeRecord(self, record: TraceRecord):
        if not self._validRecord(record):
            return False
