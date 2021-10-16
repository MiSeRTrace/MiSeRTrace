from enum import ENUM


class TraceRecord():
    pid: int
    timeStamp: float
    cpu: int
    event: str
    details: dict()

    def __init__(self, lineString: str):
        lineContents = lineString.strip().split()
        self.pid = int(lineContents[0].split('-')[-1])
        self.cpu = int(lineContents[1][1:-1])
        self.timeStamp = float(lineContents[2][:-1])
        self.event = lineContents[3][:-1]
        for content in lineContents[4:]:
            attribute, value = content.split('=')
            self.details[attribute] = value


class ThreadWakeState(ENUM):
    SLEEP = 1
    WAIT = 2
    RUN = 3
    DEAD = 4


class ThreadSchedEvent():
    timeStamp: float
    wakeState: ThreadWakeState


class Thread():

    pid: int
    container: str
    threadSchedEventList: list()
    currentSysCall: str
    recipientTraceState: dict()  # when thread acts as a destination w.r.t request
    """
        Recipient State Store (mutable - only until end point
        Popped upon end condition: both booleans true)
        Network: Definition of a state (Thread receiving a request)
        Technical Specification: Dict(STIPP:attributes) in the destiation
            State Type: Fork OR Network
            STTIP- Source: Thread, Trace, IP, Port
            Start time
            End time
            Boolean for whether response was sent: 
            Boolean for request from different STTIP

    """
    recipientTraceLog: list()  # when thread acts as a destination w.r.t request
    """
        
        Recipient Thread Log (Append - only LOG)
        Just a list of Recipient trace states

    """
    requestorTraceState: dict()  # when thread acts as a source w.r.t request (must have the reference of the same object at the destination)
    """
        Requestor State Store (
        Append only log per key (appened by the recipient only)
        Key:Value of TraceID:State Object(STTIP, attributes)
    """


class ThreadTraceState():
    srcThread: Thread
    srcIP: str
    srcPort: int
    traceID: int
    responseSentOnce: bool = 0
    newSrcObserved: bool = 0
    startTimeStamp: float
    endTimeStamp: float

    def __init__(self, srcThread: Thread, srcIP: str, srcPort: int, startTimeStamp: float):
        self.srcThread = srcThread
        self.srcIP = srcIP
        self.srcPort = srcPort
        self.endTimeStamp = self.startTimeStamp = startTimeStamp

    def setNewSrcObserved(self):
        self.newSrcObserved = True

    def setResponseSentOnce(self):
        self.responseSentOnce = True


ActiveThreadPool = dict()  # key is PID, value is a Thread object

DeadThreadPool = list()  # contains Dead Thread objects
