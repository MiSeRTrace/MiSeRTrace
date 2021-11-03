from tracethread import Thread


class ThreadState():
    def __init__(self, srcThread: Thread, handlingThread: Thread, traceID: int,
                 startTimeStamp: float):
        self.srcThread: Thread = srcThread
        self.handlingThread: Thread = handlingThread
        self.traceID: int = traceID
        self.startTimeStamp: float = startTimeStamp
        self.endTimeStamp: float = startTimeStamp  # remember to update accordingly

    def updateEndTime(self, endTimeStamp: float):
        self.endTimeStamp = endTimeStamp


class ForkThreadState(ThreadState):
    pass


class NetworkThreadState(ThreadState):
    def __init__(self, srcThread: Thread, handlingThread: Thread, traceID: int,
                 srcIP: str, srcPort: int, startTimeStamp: float):
        super(NetworkThreadState, self).__init__(srcThread, handlingThread,
                                                 traceID, startTimeStamp)
        self.srcIP: str = srcIP
        self.srcPort: int = srcPort
        self.responseSentOnce: bool = False
        self.newSrcObserved: bool = False

    def setNewSrcObserved(self):
        self.newSrcObserved = True

    def setResponseSentOnce(self):
        self.responseSentOnce = True