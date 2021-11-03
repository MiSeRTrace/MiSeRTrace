from enum import Enum
from tracerecord import *
from traceprocessor import TraceProcessor
from threadstate import ForkThreadState, NetworkThreadState


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
    def __init__(self,
                 timeStamp: float = 0,
                 wakeState: ThreadWakeState = ThreadWakeState.RUNNING):
        self.wakeState = wakeState
        self.timeStamp = timeStamp


class Thread():
    def __init__(self,
                 pid: int,
                 container: str,
                 traceProcessor: TraceProcessor,
                 currentSchedState: ThreadSchedEvent = ThreadSchedEvent()):
        self.pid = pid
        self.container = container
        self.currentSchedState: ThreadSchedEvent = currentSchedState
        self.currentSysCall: str = None  # when thread acts as a destination w.r.t request

        self.forkThreadState: list[ForkThreadState] = list()
        self.traceProcessor = traceProcessor
        self.networkThreadStates: dict[tuple, NetworkThreadState] = dict()
        """
           Network Trace States(mutable - only until end point
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
        self.intermediateThreadStates: dict[tuple, NetworkThreadState] = dict()
        self.networkThreadStateLog: list[NetworkThreadState] = list()
        # when thread acts as a destination w.r.t request
        """
           Recipient Thread Log (Append - only LOG)
           Just a list of Recipient trace states

        """

        self.destinationThreadStates: dict[int,
                                           list[NetworkThreadState
                                                or ForkThreadState]] = dict()
        # when thread acts as a source w.r.t request (must have the reference of the same object at the destination)
        """
           Requestor State Store (Append only log per key (appened by the recipient only)
           Key:Value of TraceID:State Object(STTIP, attributes)
        """

    def setCurrentSchedState(
            self,
            timeStamp: float = 0,
            wakeState: ThreadWakeState = ThreadWakeState.RUNNING):
        self.currentSchedState = ThreadSchedEvent(timeStamp, wakeState)

    def addForkThreadState(self, forkThreadState):
        self.forkThreadState.append(forkThreadState)
        forkThreadState.srcThread.setDestinationReference(
            forkThreadState.traceID, forkThreadState)

    def isCompoundForkThreadState(self):
        return len(self.forkThreadState) > 1

    def setDestinationReference(self, traceID: int, destinationReference):
        if traceID:
            self.destinationThreadStates[traceID] = destinationReference
            return True
        else:
            return False

    def consumeRecord(self, record: TraceRecord):
        #Sending message: Logic
        #   {
        #   Check if request/response	(Using socket)
        #   Create/Update Socket
        # 	Set Socket Parameters, thread
        # 	Check if destination in Recipient Trace state
        #   
        #   #Request
        # 	Update socket -> set as request
        
        # 	#Response
        # 	Update socket -> set as response
        # 	Update Current Trace State Store Booleans and accordingly push to intermediate
        # 	Update end time in both current and intermediate store
        #   }

        #     #Receiving message: Logic
        #     {
        #     	#Response
            
        #     #Request
        # If Check for front-end container
        # Insert TraceID
        # Create State(STTIP)Special case
        # Else:
        # Find sender socket
        # Find source thread
        # Create ThreadTraceState(STTIP)
        # 		Create Destination Reference
        # 	If data of same STTIP in intermediate buffer
        # 	Move state from intermediate to logs
        # If data of same STTIP in tracestatestore
        # 	Update end time (Helps in scenario where no response)

        # 	Update Current Trace State Store Booleans, and accordingly push to intermediate
        # Init Start/End
        # Add to RecipientStateStore
        # }
        # }


        


class DestinationReference():
    def __init__(self, destThread: Thread, state: NetworkThreadState
                 or ForkThreadState):
        # stores the destination state (either fork or trace)
        self.threadState: NetworkThreadState or ForkThreadState = state
        self.thread: Thread = destThread  # stores the destination thread