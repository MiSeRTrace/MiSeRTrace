from enum import Enum
from tracerecord import *
from traceprocessor import TraceProcessor
from threadstate import ForkThreadState, NetworkThreadState
from tracesocket import SocketElement, SocketStatus


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


class SendSyscallState():
    def __init__(self):
        self.inetSockSetStateObserved = False
        self.tcpProbeObserved = False
        self.request = True
        self.response = False

    def inetSockSetStateObserved(self):
        self.inetSockSetStateObserved = True

    def tcpProbeObserved(self):
        self.tcpProbeObserved = True

    def isTcpProbeObserved(self):
        return self.tcpProbeObserved

    def isInetSockSetStateObserved(self):
        return self.inetSockSetStateObserved


class RecvSyscallState():
    def __init__(self):
        pass


class Thread():
    def __init__(self,
                 pid: int,
                 container: str,
                 traceProcessor: TraceProcessor,
                 currentSchedState: ThreadSchedEvent = ThreadSchedEvent()):
        self.pid = pid
        self.container = container
        self.currentSchedState: ThreadSchedEvent = currentSchedState

        self.forkThreadState: list[ForkThreadState] = list()
        self.traceProcessor = traceProcessor
        self.networkThreadStates: dict[tuple, NetworkThreadState] = dict()  #
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

    def addNetworkThreadState(self, networkThreadState, source):
        self.networkThreadStates[source] = networkThreadState
        networkThreadState.srcThread.setDestinationReference(
            networkThreadState.traceID, networkThreadState)

    def addDestinationReference(self, traceID: int, destinationReference):
        if traceID:
            self.destinationThreadStates[traceID] = destinationReference
        else:
            print("Failed to add Destination Reference")
            exit()

    def consumeRecord(self, record: TraceRecord):
        """
        destroy sock
        Sender side create both sockets
        tcp_probe for both req and ack - check if this happens always
        Clear socket after use
        Network state based on fork
        """
        if record.event == "sys_enter_sendto":
            self.tcpState = SendSyscallState()

        if type(self.tcpState) == SendSyscallState:
            if record.event == "inet_sock_set_state":
                self.tcpState.inetSockSetStateObserved()

            if record.event == "tcp_probe":
                # Updating Socket Cookie for the second tcp_probe
                destinationIP = record.details["daddr"]
                destinationPort = record.details["dport"]
                sourceIP = record.details["saddr"]
                sourcePort = record.details["sport"]
                if self.tcpState.tcpProbeObserved(
                ) and not self.tcpState.inetSockSetStateObserved():
                    receiverSock = self.traceProcessor.socketPool.getSocket(
                        destinationIP, destinationPort, sourceIP, sourcePort)
                    self.traceProcessor.socketPool.updateSocket()
                    if receiverSock:
                        self.traceProcessor.socketPool.updateSocket(
                            receiverSock, receiverSock.socketStatus, None,
                            record.details["sock_cookie"])
                    else:
                        print(
                            "ERROR: Receiver Socket did not get created on the first TCP Probe"
                        )
                        exit()

                if not self.tcpState.isInetSockSetStateObserved(
                ) and not self.tcpState.tcpProbeObserved():
                    self.tcpState.tcpProbeObserved()
                    # Identify if request or response
                    isRequest = True
                    for networkState in self.networkThreadStates:
                        threadState = self.networkThreadStates[networkState]
                        if threadState.srcIP == destinationIP and threadState.srcPort == destinationPort:
                            isRequest = False

                    if isRequest:
                        senderSock = self.traceProcessor.socketPool.getSocket(
                            sourceIP, sourcePort, destinationIP,
                            destinationPort)
                        if not senderSock:
                            self.traceProcessor.socketPool.addSocket(
                                SocketElement(sourceIP, sourcePort,
                                              destinationIP, destinationPort,
                                              SocketStatus.REQUEST, self))
                        else:
                            self.traceProcessor.socketPool.updateSocket(
                                senderSock, SocketStatus.REQUEST, self)

                        receiverSock = self.traceProcessor.socketPool.getSocket(
                            destinationIP, destinationPort, sourceIP,
                            sourcePort)
                        if not receiverSock:
                            self.traceProcessor.socketPool.addSocket(
                                SocketElement(destinationIP, destinationPort,
                                              sourceIP, sourcePort,
                                              SocketStatus.REQUEST, None))
                        else:
                            self.traceProcessor.socketPool.updateSocket(
                                receiverSock, SocketStatus.REQUEST, None)
                    # Case where the thread is sending a response
                    else:
                        pass

            if record.event == "sys_exit_sendto":
                del (self.tcpState)
                self.tcpState = None

        # RECEIVING LOGIC
        if record.event == "sys_enter_recvfrom":
            self.tcpState = RecvSyscallState()

        if type(self.tcpState) == RecvSyscallState:

            isRequest = None
            if record.event == "tcp_rcv_space_adjust":
                # Check if Frontend container
                if record.details["saddr"] == self.traceProcessor.gatewayIP:
                    traceID = TraceProcessor.nextTraceID()
                    sourcePort = record.details["dport"]
                    networkThreadState = NetworkThreadState(
                        None, self, traceID, self.traceProcessor.gatewayIP,
                        sourcePort, record.timeStamp)
                    self.addNetworkThreadState(networkThreadState)
                else:
                    sourceIP = record.details["daddr"]
                    sourcePort = record.details["dport"]
                    destinationIP = record.details["saddr"]
                    destinationPort = record.details["sport"]
                    sourceSocket = self.traceProcessor.socketPool.getSocket(
                        sourceIP, sourcePort, destinationIP, destinationPort)
                    sourceThread = sourceSocket.srcThread
                    isRequest = False
                    if sourceSocket.socketStatus == SocketStatus.REQUEST:
                        isRequest = True

                    if isRequest:
                        incomingRequestTraces = list()
                        for networkStateKey in sourceThread.networkThreadStates:
                            incomingRequestTraces.append(networkStateKey[1])

                        # Check if a state already exists in the current network states
                        # Logic to move into intermediate
                        for networkStateKey in self.networkThreadStates:
                            sourceThreadToBeChecked = networkStateKey[0]
                            netState = self.networkThreadStates[
                                networkStateKey]
                            canBeMovedToIntermediate = netState.responseSentOnce and sourceThread != sourceThreadToBeChecked and netState.traceID in incomingRequestTraces
                            if canBeMovedToIntermediate:
                                netState.setNewSrcObserved()
                                self.intermediateThreadStates[(
                                    sourceThread, netState.traceID)] = netState

                        # Move existing state to permanent log due to it incoming request being from same source
                        for networkStateKey in self.intermediateThreadStates:
                            sourceThreadToBeChecked = networkStateKey[0]
                            netState = self.networkThreadStates[
                                networkStateKey]
                            if (sourceThread == sourceThreadToBeChecked and
                                    netState.traceID in incomingRequestTraces):
                                self.networkThreadStateLog[(
                                    sourceThread, netState.traceID)] = netState

                        # Create a child state for each (network thread state in the parent)
                        for networkStateKey in sourceThread.networkThreadStates:
                            traceID = networkStateKey[1]
                            # Checking if state already exists
                            if (sourceThread, traceID
                                ) not in self.networkThreadStates and (
                                    sourceThread, traceID
                                ) not in self.intermediateThreadStates:
                                networkThreadState = NetworkThreadState(
                                    sourceThread, self, traceID, sourceIP,
                                    sourcePort, record.timeStamp)
                                self.addNetworkThreadState(networkThreadState)

            elif record.event == "sys_exit_recvfrom":
                del (self.tcpState)
                self.tcpState = None
