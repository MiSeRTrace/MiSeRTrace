class ThreadState:
    def __init__(self, srcThread, handlingThread, traceID: int, startTimeStamp: float):
        self.srcThread = srcThread
        self.handlingThread = handlingThread
        self.traceID: int = traceID
        self.startTimeStamp: float = startTimeStamp
        self.endTimeStamp: float = startTimeStamp  # remember to update accordingly

    def updateEndTime(self, endTimeStamp: float):
        self.endTimeStamp = endTimeStamp


class ForkThreadState(ThreadState):
    pass


class NetworkThreadState(ThreadState):
    def __init__(
        self,
        srcThread,
        handlingThread,
        traceID: int,
        srcSocket,
        startTimeStamp: float,
    ):
        super(NetworkThreadState, self).__init__(
            srcThread, handlingThread, traceID, startTimeStamp
        )
        self.srcSocket = srcSocket
        self.responseSentOnce: bool = False
        self.newSrcObserved: bool = False

    def __str__(self):
        gatewayPid = "Gateway PID"
        return f"Source: {self.srcSocket.srcIp}:{self.srcSocket.srcPort} with PID {self.srcThread.pid if self.srcThread else gatewayPid}, Trace ID: {self.traceID}, Start time: {self.startTimeStamp}"

    def setNewSrcObserved(self):
        self.newSrcObserved = True

    def setResponseSentOnce(self):
        self.responseSentOnce = True

    def isNewSrcObserved(self):
        return self.newSrcObserved

    def isResponseSentOnce(self):
        return self.responseSentOnce
