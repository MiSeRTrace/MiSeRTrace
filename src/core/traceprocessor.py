from core.socketpool import *
from core.threadpool import *
from core.tracerecord import *
from core.tracethread import Thread
from core.threadstate import ForkThreadState, NetworkThreadState
from pprint import pprint
import csv
import pickle


class TraceProcessor:
    def __init__(self, inputFilePath: str, gatewayIP: str):
        self.socketPool: SocketPool = SocketPool()
        self.threadPool: ThreadPool = ThreadPool(self)
        self.traceID = 0
        self.traceGenesis = dict()
        self.lastTimeStamp = 0
        self.gatewayIP = gatewayIP
        # self.globalStateManager: GlobalStateManager = GlobalStateManager(
        #     gsClasses=gsClasses)
        self.ipStore = dict()
        self.tabCount = 0
        self.rawFormat = False
        self.colored = False
        self.recordsProcessed = 0

        with open(inputFilePath, "r") as initialThreads:
            csvReader = csv.reader(initialThreads, delimiter="|")
            for line in csvReader:
                pid, container, ip, _ = line
                pid = int(pid)
                # print(pid)
                self.ipStore[ip] = container
                self.threadPool.addThread(Thread(pid, container, ip, self))

    def dumpFirstPass(self, path: str):
        with open(path, "wb") as pickleDumpFile:
            pickle.dump(self, pickleDumpFile)

    def addTraceGenesis(self, traceID, destinationReference):
        if traceID not in self.traceGenesis:
            self.traceGenesis[traceID] = destinationReference
            return True
        return False

    def serializeTraceData(self):
        traceData: dict[tuple, dict] = dict()

        for traceId in self.traceGenesis:
            threadState = self.traceGenesis[traceId]
            traceData[
                (
                    traceId,
                    threadState.handlingThread.pid,
                    threadState.handlingThread.container,
                    threadState.handlingThread.ip,
                    threadState.startTimeStamp,
                    threadState.endTimeStamp,
                )
            ] = dict()
            if traceId in threadState.handlingThread.destinationThreadStates:
                self._recursiveFillTraceData(
                    traceId,
                    threadState.startTimeStamp,
                    threadState.handlingThread.destinationThreadStates,
                    traceData[
                        (
                            traceId,
                            threadState.handlingThread.pid,
                            threadState.handlingThread.container,
                            threadState.handlingThread.ip,
                            threadState.startTimeStamp,
                            threadState.endTimeStamp,
                        )
                    ],
                )

    def _recursiveFillTraceData(
        self,
        traceId: int,
        parentStateStartTimeStamp: float,
        destinationThreadStates: "dict[int, list[NetworkThreadState or ForkThreadState]]",
        container: "dict[tuple, dict]",
    ):
        for threadState in destinationThreadStates[traceId]:
            if threadState.startTimeStamp >= parentStateStartTimeStamp:
                if type(threadState) == ForkThreadState:
                    state = "ForkThreadState"
                else:
                    state = "NetworkThreadState"

                self.tabCount += 1

                container[
                    (
                        state,
                        threadState.handlingThread.pid,
                        threadState.handlingThread.container,
                        threadState.handlingThread.ip,
                        threadState.startTimeStamp,
                        threadState.endTimeStamp,
                    )
                ] = dict()

                if traceId in threadState.handlingThread.destinationThreadStates:
                    self._recursiveFillTraceData(
                        traceId,
                        threadState.startTimeStamp,
                        threadState.handlingThread.destinationThreadStates,
                        container[
                            (
                                state,
                                threadState.handlingThread.pid,
                                threadState.handlingThread.container,
                                threadState.handlingThread.ip,
                                threadState.startTimeStamp,
                                threadState.endTimeStamp,
                            )
                        ],
                    )
                self.tabCount -= 1

    def consumeRecord(self, record: TraceRecord):
        if not self._validRecord(record):
            return False
        if record.isImplementation:
            if "sched" in record.event:
                self.threadPool.processSchedEvents(record)
            else:
                self.processEvents(record)
        self.lastTimeStamp = record.timeStamp
        self.recordsProcessed += 1
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

    def terminate(self):
        self.threadPool.freeActiveThreadPool()
