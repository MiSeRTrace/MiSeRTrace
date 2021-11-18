from socketpool import *
from threadpool import *
from tracerecord import *
from tracethread import Thread
from globalstatemanager import GlobalStateManager


class TraceProcessor():
    def __init__(self, pathToPIDListFile: str, gatewayIP: str):
        self.socketPool: SocketPool = SocketPool()
        self.threadPool: ThreadPool = ThreadPool(self)
        self.traceID = 0
        self.traceDestinationReference = dict()
        self.gatewayIP = ",".join(
            [str(hex(int(i)))[2:].zfill(2) for i in gatewayIP.split(".")])
        # self.globalStateManager: GlobalStateManager = GlobalStateManager(
        #     gsClasses=gsClasses)
        with open(pathToPIDListFile, "r") as initialThreads:
            for line in initialThreads.readlines():
                pid, container, _ = line.strip().split()
                pid = int(pid)
                # print(pid)
                self.threadPool.addThread(
                    Thread(pid, container, self,
                           ThreadSchedState(0, ThreadWakeState.WAKING)))

    def addTraceDestinationReference(self, destinationReference,traceID):
        if traceID not in self.traceDestinationReference:
            self.traceDestinationReference[traceID]=destinationReference
            return True
        return False

    def consumeRecord(self, record: TraceRecord):
        if not self._validRecord(record):
            return False
        if 'sched' in record.event:
            self.threadPool.processSchedEvents(record)
        else:
            self.processEvents(record)
        return True

    # basic validation checks can be added here
    def _validRecord(self, record: TraceRecord):
        return True

    def processEvents(self, record: TraceRecord):
        thread: Thread = self.threadPool.getThread(record.pid)
        if thread:
            thread.consumeRecord(record)

    def nextTraceID(self):
        self.traceID += 1
        return self.traceID
