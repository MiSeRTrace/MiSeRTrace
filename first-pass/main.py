from enum import Enum
import sys
from typing import Container

DEBUG = 0


class TraceRecord():

    def __init__(self, lineString: str):
        # <idle>-0     [016] 56701.429653: sched_switch:          prev_comm=swapper/16 prev_pid=0 prev_prio=120 prev_state=0 next_comm=mongod next_pid=23939 next_prio=120
        lineContents = lineString.strip().split()
        self.pid = int(lineContents[0].split('-')[-1])  # 0 is command-pid
        # 1 is cpu in the format [cpuNo.]
        self.cpu = int(lineContents[1][1:-1])
        self.timeStamp = float(lineContents[2][:-1])  # 2 is timestamp with ':'
        self.event = lineContents[3][:-1]  # 3 is the event with ':'
        self.details = dict()  # 4 is the dictionary to store all attributes of the event
        for content in lineContents[4:]:
            attribute, value = content.split('=')
            self.details[attribute] = value


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
        self.recipientTraceState: dict = dict()
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
        self.recipientTraceLog: list()  # when thread acts as a destination w.r.t request
        """
           Recipient Thread Log (Append - only LOG)
           Just a list of Recipient trace states

       """
        self.requestorTraceState: dict(
        )  # when thread acts as a source w.r.t request (must have the reference of the same object at the destination)
        """
           Requestor State Store (Append only log per key (appened by the recipient only)
           Key:Value of TraceID:State Object(STTIP, attributes)
       """

    def __str__(self) -> str:
        return f"PID:{self.pid} Container:{self.container}"

    def updateThread(self, traceRecord: TraceRecord):
        pass


class SocketElement():

    def __init__(self, socketCookie: int, srcIP: str, destIP: str, srcPort: int, destPort: int):
        self.socketCookie = socketCookie
        self.srcIP = srcIP
        self.destIP = destIP
        self.srcPort = srcPort
        self.destPort = destPort
        self.srcThread = None
        self.destThread = None

    def updateSrcThread(self, srcThread: Thread):
        self.srcThread = srcThread

    def updateDestThread(self, destThread: Thread):
        self.destThread = destThread

# class RootEvents():


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
        self.state = state
        self.thread = destThread  # stores the destination thread


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


# Create threads which exist upon container startup
threadPool = ThreadPool()
with open("traceData/pids.txt", "r") as pidData:
    for line in pidData.readlines():
        pid, container, _ = line.strip().split()
        pid = int(pid)
        threadPool.addThread(Thread(pid, container))

if (DEBUG == 1):
    for thread in threadPool.ActiveThreadPool.values():
        print(thread)


for line in sys.stdin:
    record = TraceRecord(line)
    print(record.pid, record.cpu, record.timeStamp, record.event, record.details)
