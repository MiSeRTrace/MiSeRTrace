from enum import Enum
from tracerecord import TraceRecord


class ThreadWakeState(Enum):
    RUNNING = -1
    WAKING = 128  # W
    SLEEP = 1  # S
    RUNNABLE = 256  # R
    RUNNABLE_PLACEHOLDERS = 0  # R : Applicable only to Swappers, kworkers
    SLEEP_UNINTERRPUTABLE = 2  # D
    EXIT_ZOMBIE = 16  # Z
    EXIT_DEAD = 32  # X


class ThreadSchedEvent():

    def __init__(self, timeStamp: float = 0, wakeState: ThreadWakeState = ThreadWakeState.RUNNING):
        self.wakeState = wakeState
        self.timeStamp = timeStamp


class Thread():
    def __init__(self, pid: int, container: str, currentSchedState: ThreadSchedEvent = ThreadSchedEvent()):
        self.pid = pid
        self.container = container
        self.currentSchedState: ThreadSchedEvent = ThreadSchedEvent
        self.currentSysCall: str = None  # when thread acts as a destination w.r.t request
        self.traceStates: dict = dict()
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
           Each key-value pair in this dictionary stores the state wrt one incoming TCP connection
       """
        self.traceLog: list()  # when thread acts as a destination w.r.t request
        """
           Recipient Thread Log (Append - only LOG)
           Just a list of Recipient trace states

       """
        self.destinationTraceStates: dict(
        )  # when thread acts as a source w.r.t request (must have the reference of the same object at the destination)
        """
           Requestor State Store (Append only log per key (appened by the recipient only)
           Key:Value of TraceID:State Object(STTIP, attributes)
       """

    def __str__(self) -> str:
        return f"PID:{self.pid} Container:{self.container}"

    def updateThread(self, traceRecord: TraceRecord):
        pass


class ThreadForkState():

    def __init__(self,  srcThread: Thread, traceID: int, startTimeStamp: float):
        self.srcThread: Thread = srcThread
        self.traceID: int = traceID
        self.startTimeStamp: float = startTimeStamp
        self.endTimeStamp: float = startTimeStamp  # remember to update accordingly

    def updateEndTime(self, endTimeStamp: float):
        self.endTimeStamp = endTimeStamp


class ThreadTraceState():

    def __init__(self, srcThread: Thread, traceID: int, srcIP: str, srcPort: int, startTimeStamp: float):
        self.srcThread: Thread = srcThread
        self.srcIP: str = srcIP
        self.srcPort: int = srcPort
        self.traceID: int = traceID
        self.endTimeStamp: float = startTimeStamp  # remember to update accordingly
        self.startTimeStamp: float = startTimeStamp
        self.responseSentOnce: bool = 0
        self.newSrcObserved: bool = 0

    def setNewSrcObserved(self):
        self.newSrcObserved = True

    def setResponseSentOnce(self):
        self.responseSentOnce = True

    def updateEndTime(self, endTimeStamp: float):
        self.endTimeStamp = endTimeStamp


class DestinationReference():

    def __init__(self, destThread: Thread, state: ThreadTraceState or ThreadForkState):
        # stores the destination state (either fork or trace)
        self.state: ThreadTraceState or ThreadForkState = state
        self.thread = destThread  # stores the destination thread


if __name__ == "__main__":
    TraceRecord
