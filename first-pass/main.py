from enum import Enum
import sys

class TraceRecord():

    def __init__(self, lineString: str):
        lineContents = lineString.strip().split()
        self.pid = int(lineContents[0].split('-')[-1])
        self.cpu = int(lineContents[1][1:-1])
        self.timeStamp = float(lineContents[2][:-1])
        self.event = lineContents[3][:-1]
        self.details = dict()
        for content in lineContents[4:]:
            attribute, value = content.split('=')
            self.details[attribute] = value


class ThreadWakeState(Enum):
    UNKNOWN = -1
    SLEEP = 1
    WAIT = 2
    RUN = 3
    DEAD = 4


class ThreadSchedEvent():

    def __init__(self, timeStamp: float, wakeState: ThreadWakeState = ThreadWakeState.UNKNOWN):
        self.wakeState = wakeState
        self.timeStamp = timeStamp


class Thread():
    # threadSchedEventList: list = list()
    currentSchedState: ThreadSchedEvent
    currentSysCall: str = None  # when thread acts as a destination w.r.t request
    recipientTraceState: dict = dict()
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
        Requestor State Store (Append only log per key (appened by the recipient only)
        Key:Value of TraceID:State Object(STTIP, attributes)
    """

    def __init__(self, pid: int, container: str):
        self.pid = pid
        self.container = container

# class RootEvents():


class ThreadTraceState():

    def __init__(self, srcThread: Thread, traceID: int, srcIP: str, srcPort: int, startTimeStamp: float):
        self.srcThread: Thread = srcThread
        self.srcIP: str = srcIP
        self.srcPort: int = srcPort
        self.traceID: int = traceID
        self.endTimeStamp: int = startTimeStamp
        self.startTimeStamp: int = startTimeStamp
        self.responseSentOnce: bool = 0
        self.newSrcObserved: bool = 0

    def setNewSrcObserved(self):
        self.newSrcObserved = True

    def setResponseSentOnce(self):
        self.responseSentOnce = True


class ThreadPool():
    ActiveThreadPool = dict()  # key is PID, value is a Thread object
    DeadThreadPool = list()  # contains Dead Thread objects

    def freeActiveThreadPool(self):
        for key in list(self.ActiveThreadPool.keys()):
            self.DeadThreadPool.append(self.ActiveThreadPool.pop(key))

    def addThread(self, newThread: Thread):
        if newThread.pid not in self.ActiveThreadPool:
            self.ActiveThreadPool[newThread.pid] = newThread
            return True
        return False

    def killThread(self, killThread: Thread):
        if killThread.pid in self.ActiveThreadPool:
            self.DeadThreadPool.append(
                self.ActiveThreadPool.pop(killThread.pid))
            return True
        return False

    def killPid(self, killPid: int):
        if killPid in self.ActiveThreadPool:
            self.DeadThreadPool.append(self.ActiveThreadPool.pop(killPid))
            return True
        return False

# pass input of report (raw format) through "sed -E 's/,\s*/,/g'""

for line in sys.stdin:
    record = TraceRecord(line)
    print(record.pid, record.cpu, record.timeStamp, record.event, record.details)
