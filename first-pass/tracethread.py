from enum import Enum
from tracerecord import *
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


class ThreadSchedState():
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

    def setInetSockSetStateObserved(self):
        self.inetSockSetStateObserved = True

    def setTcpProbeObserved(self):
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
                 traceProcessor,
                 currentSchedState: ThreadSchedState = ThreadSchedState()):
        self.pid = pid
        self.container = container
        self.traceProcessor = traceProcessor
        self.currentSchedState: ThreadSchedState = currentSchedState

        self.forkThreadStates: list[ForkThreadState] = list()
        self.networkThreadStates: dict[tuple, NetworkThreadState] = dict()
        # tuple - (srcThread, traceID)
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
        self.tcpState = RecvSyscallState()

    def setCurrentSchedState(
            self,
            timeStamp: float = 0,
            wakeState: ThreadWakeState = ThreadWakeState.RUNNING):
        self.currentSchedState.timeStamp = timeStamp
        self.currentSchedState.wakeState = wakeState

    def addForkThreadState(self, forkThreadState: ForkThreadState):
        self.forkThreadStates.append(forkThreadState)
        forkThreadState.srcThread.addDestinationReference(
            forkThreadState.traceID, forkThreadState)

    def addNetworkThreadState(self, networkThreadState: NetworkThreadState,
                              key):
        self.networkThreadStates[key] = networkThreadState
        networkThreadState.srcThread.addDestinationReference(
            networkThreadState.traceID, networkThreadState)

    def addRootNetworkThreadState(self, networkThreadState: NetworkThreadState,
                                  key, traceProcessor):
        self.networkThreadStates[key] = networkThreadState
        traceProcessor.addTraceDestinationReference(networkThreadState,networkThreadState.traceID)


    def addDestinationReference(self, traceID: int, destinationReference):
        if traceID not in self.destinationThreadStates:
            self.destinationThreadStates[traceID] = list()
        self.destinationThreadStates[traceID].append(destinationReference)

    def consumeRecord(self, record: TraceRecord):
        """
        destroy sock
        Sender side create both sockets
        tcp_probe for both req and ack - check if this happens always
        Clear socket after use
        Network state based on fork
        """
        if record.event in [
                "sys_enter_sendto", "sys_enter_write", "sys_enter_sendmsg"
        ]:
            self.tcpState = SendSyscallState()

        elif type(self.tcpState) == SendSyscallState:
            if record.event == "inet_sock_set_state":
                self.tcpState.setInetSockSetStateObserved()
                """
                Sometimes, the packet is sent through when a TCP connection is established using "inet_sock_set_state"
                "tcp_probe" event is not observed.
                Hence, whenever a new TCP connection is established, we create/set the socket state as request. 
                """
                if record.details["newstate"] == '1':
                    destinationIP = record.details["saddr"]
                    destinationPort = record.details["sport"]
                    sourceIP = record.details["daddr"]
                    sourcePort = record.details["dport"]
                    senderSock = self.traceProcessor.socketPool.getSocket(
                        sourceIP, sourcePort, destinationIP, destinationPort)
                    if not senderSock:
                        print("Sender add sock - sender sock", sourceIP,
                              sourcePort, destinationIP, destinationPort)
                        self.traceProcessor.socketPool.addSocket(
                            SocketElement(sourceIP, sourcePort, destinationIP,
                                          destinationPort,
                                          SocketStatus.REQUEST, self))
                    else:
                        self.traceProcessor.socketPool.updateSocket(
                            senderSock, SocketStatus.REQUEST, self)
                    receiverSock = self.traceProcessor.socketPool.getSocket(
                        destinationIP, destinationPort, sourceIP, sourcePort)
                    print("Sender get sock - receiver sock", destinationIP,
                          destinationPort, sourceIP, sourcePort)
                    if not receiverSock:
                        print("Sender add sock - receiver sock", destinationIP,
                              destinationPort, sourceIP, sourcePort)
                        self.traceProcessor.socketPool.addSocket(
                            SocketElement(destinationIP, destinationPort,
                                          sourceIP, sourcePort,
                                          SocketStatus.RESPONSE, None))
                    else:
                        self.traceProcessor.socketPool.updateSocket(
                            receiverSock, SocketStatus.RESPONSE, None)

            elif record.event == "tcp_probe":
                # Updating Socket Cookie for the second tcp_probe
                if not self.tcpState.isInetSockSetStateObserved(
                ) and not self.tcpState.isTcpProbeObserved():

                    destinationIP = record.details["saddr"]
                    destinationPort = record.details["sport"]
                    sourceIP = record.details["daddr"]
                    sourcePort = record.details["dport"]

                    self.tcpState.setTcpProbeObserved()

                    senderSock = self.traceProcessor.socketPool.getSocket(
                        sourceIP, sourcePort, destinationIP, destinationPort)

                    # Identify if request or response
                    isRequest = True
                    for networkState in self.networkThreadStates:
                        threadState = self.networkThreadStates[networkState]
                        if threadState.srcIP == destinationIP and threadState.srcPort == destinationPort:
                            isRequest = False
                    if isRequest:
                        print(
                            f"{self.container, record.pid} sending request at time {record.timeStamp} from {sourceIP, sourcePort, destinationIP, destinationPort}"
                        )
                        print("Sender get sock - sender sock", sourceIP,
                              sourcePort, destinationIP, destinationPort)
                        if not senderSock:
                            print("Sender add sock - sender sock", sourceIP,
                                  sourcePort, destinationIP, destinationPort)
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
                        print("Sender get sock - receiver sock", destinationIP,
                              destinationPort, sourceIP, sourcePort)
                        if not receiverSock:
                            print("Sender add sock - receiver sock",
                                  destinationIP, destinationPort, sourceIP,
                                  sourcePort)
                            self.traceProcessor.socketPool.addSocket(
                                SocketElement(destinationIP, destinationPort,
                                              sourceIP, sourcePort,
                                              SocketStatus.RESPONSE, None))
                        else:
                            self.traceProcessor.socketPool.updateSocket(
                                receiverSock, SocketStatus.RESPONSE, None)

                        print("----------------------")

                    # Case where the thread is sending a response
                    else:
                        senderSock = self.traceProcessor.socketPool.getSocket(
                            sourceIP, sourcePort, destinationIP,
                            destinationPort)
                        if not senderSock:
                            print(
                                "ERROR: Socket to send response was not found")
                            exit()
                        else:
                            # Add the thread object to the socket, update socket status to be a response
                            self.traceProcessor.socketPool.updateSocket(
                                senderSock, SocketStatus.RESPONSE, self)
                            """
                            Get the X object
                                Opposite socket's source thread
                            Use X object as key in the Y's network thread states
                            Update boolean - response sent
                            Update end time in current and intermediate stores
                            Move to intermediate if another request has arrived
                            """

                            destinationSock = self.traceProcessor.socketPool.getSocket(
                                destinationIP, destinationPort, sourceIP,
                                sourcePort)
                            destinationThread = destinationSock.srcThread

                            for networkStateKey in self.intermediateThreadStates:
                                if networkStateKey[0] == destinationThread:
                                    threadState = self.intermediateThreadStates[
                                        networkStateKey]
                                    threadState.updateEndTime(record.timeStamp)

                            threadStateToPop = list()
                            for networkStateKey in self.networkThreadStates:
                                if networkStateKey[0] == destinationThread:
                                    threadState = self.networkThreadStates[
                                        networkStateKey]
                                    threadState.setResponseSentOnce()
                                    threadState.updateEndTime(record.timeStamp)
                                    if threadState.isNewSrcObserved(
                                    ) and threadState.isResponseSentOnce():
                                        self.intermediateThreadStates[
                                            networkStateKey] = threadState
                                        threadStateToPop.append(
                                            networkStateKey)
                            for networkStateKey in threadStateToPop:
                                self.networkThreadStates.pop(networkState)

            elif record.event in [
                    "sys_exit_sendto", "sys_exit_write", "sys_exit_sendmsg"
            ]:
                del (self.tcpState)
                self.tcpState = None

        # RECEIVING LOGIC
        elif record.event in [
                "sys_enter_recvfrom", "sys_enter_read", "sys_enter_recvmsg"
        ]:
            self.tcpState = RecvSyscallState()

        elif type(self.tcpState) == RecvSyscallState:
            if record.event == "tcp_rcv_space_adjust":
                # Check if Frontend container
                # print(record.details["daddr"])
                # print(self.traceProcessor.gatewayIP)
                # print(record.timeStamp)
                #TODO Reference to openresty state from traceprocessor
                if record.details["daddr"] == self.traceProcessor.gatewayIP:
                    traceID = self.traceProcessor.nextTraceID()
                    sourcePort = record.details["dport"]
                    networkThreadState = NetworkThreadState(
                        None, self, traceID, self.traceProcessor.gatewayIP,
                        sourcePort, record.timeStamp)
                    # No reference to source thread as the source thread is docker gateway
                    self.addRootNetworkThreadState(networkThreadState,
                                                   (None, traceID),
                                                   self.traceProcessor)
                    print(
                        f"{self.container, record.pid} receiving request at time {record.timeStamp} from {record.details['daddr']}"
                    )
                    print("------------------------")
                else:
                    sourceIP = record.details["daddr"]
                    sourcePort = record.details["dport"]
                    destinationIP = record.details["saddr"]
                    destinationPort = record.details["sport"]
                    sourceSocket = self.traceProcessor.socketPool.getSocket(
                        sourceIP, sourcePort, destinationIP, destinationPort)
                    print("JUST IN CASE", self.container, record.pid,
                          record.timeStamp, sourceIP, sourcePort,
                          destinationIP, destinationPort)
                    sourceThread = sourceSocket.srcThread

                    isRequest = False
                    if sourceSocket.socketStatus == SocketStatus.REQUEST:
                        isRequest = True

                    if isRequest:
                        incomingRequestTraces = list()
                        # print(record.timeStamp)
                        print(
                            f"{self.container, record.pid} receiving request at time {record.timeStamp} using socket {sourceIP, sourcePort, destinationIP, destinationPort}"
                        )
                        print("Receiver get sock", sourceIP, sourcePort,
                              destinationIP, destinationPort)
                        print("--------------------------")
                        for networkStateKey in sourceThread.networkThreadStates:
                            incomingRequestTraces.append(networkStateKey[1])

                        # Check if a state already exists in the current network states
                        # Logic to move into intermediate
                        threadToPop = list()
                        for networkStateKey in self.networkThreadStates:
                            sourceThreadToBeChecked = networkStateKey[0]
                            netState = self.networkThreadStates[
                                networkStateKey]
                            if sourceThread != sourceThreadToBeChecked and netState.traceID not in incomingRequestTraces:
                                netState.setNewSrcObserved()
                            if netState.responseSentOnce and netState.isNewSrcObserved(
                            ):
                                self.intermediateThreadStates[(
                                    sourceThread, netState.traceID)] = netState
                                threadToPop.append(networkStateKey)
                        # Removing all the threads from activethreadstate which got moved to intermediate store
                        for networkStateKey in threadToPop:
                            self.networkThreadStates.pop(networkStateKey)

                        # Move existing state to permanent log due to it incoming request being from same source
                        for networkStateKey in self.intermediateThreadStates:
                            sourceThreadToBeChecked = networkStateKey[0]
                            netState = self.intermediateThreadStates[
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
                                self.addNetworkThreadState(
                                    networkThreadState,
                                    (sourceThread, traceID))

                        # Create a child state for each (fork thread state in the parent)
                        for forkState in sourceThread.forkThreadStates:
                            forkTraceID = forkState.traceID
                            # Assuming two threads with the same parent, do not send requests over TCP between them
                            if (sourceThread, forkTraceID
                                ) not in self.networkThreadStates and (
                                    sourceThread, forkTraceID
                                ) not in self.intermediateThreadStates:
                                networkThreadState = NetworkThreadState(
                                    sourceThread, self, forkTraceID, sourceIP,
                                    sourcePort, record.timeStamp)
                                self.addNetworkThreadState(
                                    networkThreadState,
                                    (sourceThread, forkTraceID))

            elif record.event in [
                    "sys_exit_recvfrom", "sys_exit_read", "sys_exit_recvmsg"
            ]:
                del (self.tcpState)
                self.tcpState = None
