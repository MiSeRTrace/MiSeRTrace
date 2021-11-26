from socketpool import *
from threadpool import *
from tracerecord import *
from tracethread import Thread
from threadstate import ForkThreadState, NetworkThreadState
from globalstatemanager import GlobalStateManager
import json


class TraceProcessor:
    def __init__(self, inputFilePath: str, gatewayIP: str):
        self.socketPool: SocketPool = SocketPool()
        self.threadPool: ThreadPool = ThreadPool(self)
        self.traceID = 0
        self.traceGenesis = dict()
        self.gatewayIP = ",".join(
            [str(hex(int(i)))[2:].zfill(2) for i in gatewayIP.split(".")]
        )
        # self.globalStateManager: GlobalStateManager = GlobalStateManager(
        #     gsClasses=gsClasses)

        with open(inputFilePath, "r") as initialThreads:
            for line in initialThreads.readlines():
                pid, container, ip ,_ = line.strip().split()
                pid = int(pid)
                # print(pid)
                self.threadPool.addThread(
                    Thread(
                        pid,
                        container,
                        ip,
                        self,
                        ThreadSchedState(0, ThreadWakeState.WAKING),
                    )
                )

    def addTraceGenesis(self, traceID, destinationReference):
        if traceID not in self.traceGenesis:
            self.traceGenesis[traceID] = destinationReference
            return True
        return False

    def serializeTraceData(self):
        traceData : dict[tuple, dict] = dict()
        for traceId in self.traceGenesis:
            threadState = self.traceGenesis[traceId]
            traceData[(traceId, threadState.handlingThread.pid, threadState.handlingThread.container, threadState.handlingThread.ip, threadState.startTimeStamp, threadState.endTimeStamp)] = dict()
            self.recursiveFillTraceData(traceId, threadState.handlingThread.destinationThreadStates, 
                                        traceData[(traceId, threadState.handlingThread.pid, threadState.handlingThread.container, threadState.handlingThread.ip, threadState.startTimeStamp, threadState.endTimeStamp)])
        with open("traceData.json", "w") as outfile:
            json.dump(traceData, outfile)

    def recursiveFillTraceData(self, traceId, destinationThreadStates : dict[int, list[NetworkThreadState or ForkThreadState]], 
                                    container : dict[tuple, dict]):
        for threadState in destinationThreadStates[traceId]:
            container[(threadState.handlingThread.pid, threadState.handlingThread.container, threadState.handlingThread.ip, threadState.startTimeStamp, threadState.endTimeStamp)] = dict()
            self.recursiveFillTraceData(threadState.handlingThread.destinationThreadStates[traceId], 
                                        container[(threadState.handlingThread.pid, threadState.handlingThread.container, threadState.handlingThread.ip, threadState.startTimeStamp, threadState.endTimeStamp)])

    def consumeRecord(self, record: TraceRecord):
        if not self._validRecord(record):
            return False
        if "sched" in record.event:
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

    def terminate(self):
        self.threadPool.freeActiveThreadPool()
