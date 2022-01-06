from core.socketpool import *
from core.threadpool import *
from core.tracerecord import *
from core.tracethread import Thread
from core.threadstate import ForkThreadState, NetworkThreadState
from pprint import pprint
import pickle


class bcolors:
    PINK = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    GETSOCK = "\033[38;5;175m"
    ADDSOCK = "\033[38;5;175m"


class TraceProcessor:
    def __init__(self, inputFilePath: str, gatewayIP: str):
        self.socketPool: SocketPool = SocketPool()
        self.threadPool: ThreadPool = ThreadPool(self)
        self.traceID = 0
        self.traceGenesis = dict()
        self.lastTimeStamp = 0
        self.gatewayIP = ",".join(
            [str(hex(int(i)))[2:].zfill(2) for i in gatewayIP.split(".")]
        )
        # self.globalStateManager: GlobalStateManager = GlobalStateManager(
        #     gsClasses=gsClasses)
        self.ipStore = dict()
        self.tabCount = 0
        self.rawFormat = False
        self.colored = False

        with open(inputFilePath, "r") as initialThreads:
            for line in initialThreads.readlines():
                pid, container, ip, _ = line.strip().split()
                pid = int(pid)
                # print(pid)
                self.ipStore[
                    ",".join([str(hex(int(i)))[2:].zfill(2) for i in ip.split(".")])
                ] = container
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
                if not self.rawFormat:
                    if self.colored:
                        print(
                            self.tabCount * "\t",
                            bcolors.PINK,
                            traceId,
                            bcolors.BLUE,
                            bcolors.BOLD,
                            threadState.handlingThread.container,
                            "at time",
                            bcolors.GREEN,
                            threadState.startTimeStamp,
                            "to",
                            bcolors.RED,
                            threadState.endTimeStamp,
                        )
                    else:
                        print(
                            self.tabCount * "\t",
                            traceId,
                            threadState.handlingThread.container,
                            "at time",
                            threadState.startTimeStamp,
                            "to",
                            threadState.endTimeStamp,
                        )
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

        if self.rawFormat:
            pprint(traceData)

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
                if state == "ForkThreadState":
                    printState = "Fork"
                else:
                    printState = "Net"
                if traceId in threadState.handlingThread.destinationThreadStates:
                    if not self.rawFormat:
                        if self.colored:
                            print(
                                self.tabCount * "\t",
                                bcolors.BOLD,
                                bcolors.PINK,
                                traceId,
                                bcolors.BOLD
                                + bcolors.YELLOW
                                + printState
                                + bcolors.ENDC,
                                bcolors.BOLD,
                                bcolors.BLUE,
                                threadState.handlingThread.container,
                                bcolors.ENDC,
                                "at time",
                                bcolors.GREEN,
                                threadState.startTimeStamp,
                                bcolors.ENDC,
                                "to",
                                bcolors.RED,
                                threadState.endTimeStamp,
                            )
                        else:
                            print(
                                self.tabCount * "\t",
                                traceId,
                                printState,
                                threadState.handlingThread.container,
                                "at time",
                                threadState.startTimeStamp,
                                "to",
                                threadState.endTimeStamp,
                            )

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
        if "sched" in record.event:
            self.threadPool.processSchedEvents(record)
        else:
            self.processEvents(record)
        self.lastTimeStamp = record.timeStamp
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
