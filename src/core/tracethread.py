from enum import Enum
from core.tracerecord import *
from core.threadstate import ForkThreadState, NetworkThreadState
from core.tracesocket import SocketElement, SocketStatus


class bcolors:
    PINK = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    GETSOCK = "\033[38;5;175m"
    ADDSOCK = "\033[38;5;175m"


class SendSyscallState:
    def __init__(self, startTime: float):
        # self.inetSockSetStateObserved = False
        # self.tcpProbeObserved = False
        self.request = True
        self.response = False
        self.startTime = startTime

    # def setInetSockSetStateObserved(self):
    #     self.inetSockSetStateObserved = True

    # def setTcpProbeObserved(self):
    #     self.tcpProbeObserved = True

    # def isTcpProbeObserved(self):
    #     return self.tcpProbeObserved

    # def isInetSockSetStateObserved(self):
    #     return self.inetSockSetStateObserved


class RecvSyscallState:
    def __init__(self, startTime: float):
        self.startTime = startTime


class Thread:
    def __init__(self, pid: int, container: str, ip: str, traceProcessor):
        self.pid = pid
        self.container = container
        self.ip = ip
        self.traceProcessor = traceProcessor

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

        self.destinationThreadStates: dict[
            int, list[NetworkThreadState or ForkThreadState]
        ] = dict()
        # when thread acts as a source w.r.t request (must have the reference of the same object at the destination)
        """
           Requestor State Store (Append only log per key (appened by the recipient only)
           Key:Value of TraceID:State Object(STTIP, attributes)
        """
        self.tcpState = RecvSyscallState(0)

    def addForkThreadState(self, forkThreadState: ForkThreadState):
        self.forkThreadStates.append(forkThreadState)
        forkThreadState.srcThread.addDestinationReference(
            forkThreadState.traceID, forkThreadState
        )

    def addNetworkThreadState(self, networkThreadState: NetworkThreadState, key):
        self.networkThreadStates[key] = networkThreadState
        networkThreadState.srcThread.addDestinationReference(
            networkThreadState.traceID, networkThreadState
        )

    def addDestinationReference(self, traceID: int, destinationReference):
        if traceID not in self.destinationThreadStates:
            self.destinationThreadStates[traceID] = list()
        self.destinationThreadStates[traceID].append(destinationReference)

    def addRootNetworkThreadState(self, networkThreadState: NetworkThreadState, key):
        self.networkThreadStates[key] = networkThreadState
        self.traceProcessor.addTraceGenesis(
            networkThreadState.traceID, networkThreadState
        )

    def consumeRecord(self, record: TraceRecord):
        if (
            record.event
            in [
                "sys_enter_sendto",
                "sys_enter_write",
                "sys_enter_sendmsg",
                "sys_enter_writev",
            ]
            and (len(self.networkThreadStates) or len(self.forkThreadStates))
        ):
            self.tcpState = SendSyscallState(record.timeStamp)

        elif type(self.tcpState) == SendSyscallState:
            # if record.event == "inet_sock_set_state":
            #     self.tcpState.setInetSockSetStateObserved()

            #     # Sometimes, the packet is sent through when a TCP connection is established using "inet_sock_set_state"
            #     # "tcp_probe" event is not observed.
            #     # Hence, whenever a new TCP connection is established, we create/set the socket state as request.
            #     # In the raw format of trace-cmd report, newstate = 1 --> TCP_ESTABLISHED

            #     if record.details["newstate"] == "1":
            #         if record.details["oldstate"] == "2":  # TCP_SYN_SENT
            #             sourceIP = record.details["saddr"]
            #             sourcePort = record.details["sport"]
            #             destinationIP = record.details["daddr"]
            #             destinationPort = record.details["dport"]
            #         elif record.details["oldstate"] == "3":  # TCP_SYN_RECV
            #             destinationIP = record.details["saddr"]
            #             destinationPort = record.details["sport"]
            #             sourceIP = record.details["daddr"]
            #             sourcePort = record.details["dport"]

            #         if self.traceProcessor.toPrint:
            #             print(
            #                 f"{bcolors.BOLD}{bcolors.BLUE}{self.container}@{record.pid}{bcolors.ENDC}{bcolors.BOLD}{bcolors.GREEN} sending request{bcolors.ENDC} at time {record.timeStamp}{bcolors.RED} from {sourceIP, sourcePort}{bcolors.YELLOW} to {destinationIP, destinationPort}"
            #             )

            #         senderSock = self.traceProcessor.socketPool.getSocket(
            #             sourceIP, sourcePort, destinationIP, destinationPort
            #         )
            #         if not senderSock:
            #             self.traceProcessor.socketPool.addSocket(
            #                 SocketElement(
            #                     sourceIP,
            #                     sourcePort,
            #                     destinationIP,
            #                     destinationPort,
            #                     SocketStatus.REQUEST,
            #                     self,
            #                 )
            #             )
            #         else:
            #             self.traceProcessor.socketPool.updateSocket(
            #                 senderSock, SocketStatus.REQUEST, self
            #             )

            #         receiverSock = self.traceProcessor.socketPool.getSocket(
            #             destinationIP, destinationPort, sourceIP, sourcePort
            #         )
            #         if not receiverSock:
            #             self.traceProcessor.socketPool.addSocket(
            #                 SocketElement(
            #                     destinationIP,
            #                     destinationPort,
            #                     sourceIP,
            #                     sourcePort,
            #                     SocketStatus.RESPONSE,
            #                     None,
            #                 )
            #             )
            #         else:
            #             self.traceProcessor.socketPool.updateSocket(
            #                 receiverSock, SocketStatus.RESPONSE, None
            #             )

            if record.event == "tcp_send":
                destinationIP = record.details["daddr"]
                destinationPort = record.details["dport"]
                sourceIP = record.details["saddr"]
                sourcePort = record.details["sport"]

                # self.tcpState.setTcpProbeObserved()
                if destinationIP == self.traceProcessor.gatewayIP:
                    for key in list(
                        filter(
                            lambda key: key[0] == None,
                            self.networkThreadStates.keys(),
                        )
                    ):
                        self.intermediateThreadStates[
                            key
                        ] = self.networkThreadStates.pop(key)
                        self.intermediateThreadStates[key].updateEndTime(
                            record.timeStamp
                        )
                    for key in list(
                        filter(
                            lambda key: key[0] == None,
                            self.intermediateThreadStates.keys(),
                        )
                    ):
                        self.intermediateThreadStates[key].updateEndTime(
                            record.timeStamp
                        )
                    if self.traceProcessor.toPrint:
                        if self.traceProcessor.colored:
                            print(
                                f"{bcolors.BOLD}{bcolors.BLUE}{self.container}@{record.pid}{bcolors.ENDC}{bcolors.BOLD}{bcolors.GREEN} sending response{bcolors.ENDC} at time {record.timeStamp}{bcolors.RED} from {sourceIP, sourcePort}{bcolors.YELLOW} to {destinationIP, destinationPort}"
                            )
                        else:
                            print(
                                f"{self.container}@{record.pid} sending response at time {record.timeStamp} from {sourceIP, sourcePort} to {destinationIP, destinationPort}"
                            )

                # If destination isn't gateway
                # elif sourceIP == self.ip:
                else:
                    senderSock = self.traceProcessor.socketPool.getSocket(
                        sourceIP, sourcePort, destinationIP, destinationPort
                    )

                    # Identify if request or response
                    isRequest = True
                    for networkStateKey in self.networkThreadStates:
                        threadState = self.networkThreadStates[networkStateKey]
                        if (
                            threadState.srcSocket.srcIp == destinationIP
                            and threadState.srcSocket.srcPort == destinationPort
                            and threadState.srcSocket.destIp == sourceIP
                            and threadState.srcSocket.destPort == sourcePort
                        ):
                            isRequest = False
                            break
                    if isRequest:
                        if self.traceProcessor.toPrint:
                            if self.traceProcessor.colored:
                                print(
                                    f"{bcolors.BOLD}{bcolors.BLUE}{self.container}@{record.pid}{bcolors.ENDC}{bcolors.BOLD}{bcolors.GREEN} sending request{bcolors.ENDC} at time {record.timeStamp}{bcolors.RED} from {sourceIP, sourcePort}{bcolors.YELLOW} to {destinationIP, destinationPort}"
                                )
                            else:
                                print(
                                    f"{self.container}@{record.pid} sending request at time {record.timeStamp} from {sourceIP, sourcePort} to {destinationIP, destinationPort}"
                                )

                        if not senderSock:
                            self.traceProcessor.socketPool.addSocket(
                                SocketElement(
                                    sourceIP,
                                    sourcePort,
                                    destinationIP,
                                    destinationPort,
                                    SocketStatus.REQUEST,
                                    self,
                                )
                            )
                        else:
                            self.traceProcessor.socketPool.updateSocket(
                                senderSock, SocketStatus.REQUEST, self
                            )

                        receiverSock = self.traceProcessor.socketPool.getSocket(
                            destinationIP, destinationPort, sourceIP, sourcePort
                        )
                        if not receiverSock:
                            self.traceProcessor.socketPool.addSocket(
                                SocketElement(
                                    destinationIP,
                                    destinationPort,
                                    sourceIP,
                                    sourcePort,
                                    SocketStatus.RESPONSE,
                                    None,
                                )
                            )
                        else:
                            self.traceProcessor.socketPool.updateSocket(
                                receiverSock, SocketStatus.RESPONSE, None
                            )

                    # Case where the thread is sending a response
                    else:
                        if self.traceProcessor.toPrint:
                            if self.traceProcessor.colored:
                                print(
                                    f"{bcolors.BOLD}{bcolors.BLUE}{self.container}@{record.pid}{bcolors.ENDC}{bcolors.BOLD}{bcolors.GREEN} sending response{bcolors.ENDC} at time {record.timeStamp}{bcolors.RED} from {sourceIP, sourcePort}{bcolors.YELLOW} to {destinationIP, destinationPort}"
                                )
                            else:
                                print(
                                    f"{self.container}@{record.pid} sending response at time {record.timeStamp} from {sourceIP, sourcePort} to {destinationIP, destinationPort}"
                                )

                        if not senderSock:
                            print(record.timeStamp, record.command, record.details)
                            print(sourceIP, sourcePort, destinationIP, destinationPort)
                            print("ERROR: Socket to send response was not found")
                            print(len(self.traceProcessor.traceGenesis))
                            # for key in self.networkThreadStates:
                            #     print("Source PID", key[0].pid)
                            #     print(self.networkThreadStates[key])
                            exit()
                        else:
                            # Add the thread object to the socket, update socket status to be a response
                            self.traceProcessor.socketPool.updateSocket(
                                senderSock, SocketStatus.RESPONSE, self
                            )

                            # Get the X object
                            #     Opposite socket's source thread
                            # Use X object as key in the Y's network thread states
                            # Update boolean - response sent
                            # Update end time in current and intermediate stores
                            # Move to intermediate if another request has arrived

                            receiverSock = self.traceProcessor.socketPool.getSocket(
                                destinationIP,
                                destinationPort,
                                sourceIP,
                                sourcePort,
                            )
                            if not receiverSock:
                                print(
                                    "ERROR: Currently sending response, however socket which sent trequest not found sock not found for sending response"
                                )
                                exit()
                            destinationThread = receiverSock.srcThread
                            tracesInParent = list()
                            for (
                                networkStateKey
                            ) in destinationThread.networkThreadStates:
                                destState = destinationThread.networkThreadStates[
                                    networkStateKey
                                ]
                                tracesInParent.append(destState.traceID)

                            for networkStateKey in self.intermediateThreadStates:
                                if (
                                    networkStateKey[0] == destinationThread
                                    and networkStateKey[2] == destinationIP
                                    and networkStateKey[3] == destinationPort
                                    and networkStateKey[1] in tracesInParent
                                ):
                                    threadState = self.intermediateThreadStates[
                                        networkStateKey
                                    ]
                                    threadState.updateEndTime(record.timeStamp)

                            threadStateToPop = list()
                            for networkStateKey in self.networkThreadStates:
                                if (
                                    networkStateKey[0] == destinationThread
                                    and networkStateKey[2] == destinationIP
                                    and networkStateKey[3] == destinationPort
                                ):
                                    threadState = self.networkThreadStates[
                                        networkStateKey
                                    ]
                                    threadState.setResponseSentOnce()
                                    threadState.updateEndTime(record.timeStamp)
                                    if threadState.isNewSrcObserved():
                                        self.intermediateThreadStates[
                                            networkStateKey
                                        ] = threadState
                                        threadStateToPop.append(networkStateKey)
                            for networkStateKey in threadStateToPop:
                                self.networkThreadStates.pop(networkStateKey)

            elif record.event in [
                "sys_exit_sendto",
                "sys_exit_write",
                "sys_exit_sendmsg",
                "sys_exit_writev",
            ]:
                del self.tcpState
                self.tcpState = None

        # RECEIVING LOGIC
        elif record.event in [
            "sys_enter_recvfrom",
            "sys_enter_read",
            "sys_enter_recvmsg",
            "sys_enter_readv",
        ]:
            self.tcpState = RecvSyscallState(record.timeStamp)

        elif type(self.tcpState) == RecvSyscallState:
            if record.event == "tcp_rcv_space_adjust":
                # Check if Frontend container
                if record.details["daddr"] == self.traceProcessor.gatewayIP:
                    if not len(
                        list(
                            filter(
                                lambda key: key[0] == None,
                                self.networkThreadStates.keys(),
                            )
                        )
                    ):
                        for key in list(
                            filter(
                                lambda key: key[0] == None,
                                self.intermediateThreadStates.keys(),
                            )
                        ):
                            self.networkThreadStateLog.append(
                                self.intermediateThreadStates.pop(key)
                            )
                        traceID = self.traceProcessor.nextTraceID()
                        sourcePort = record.details["dport"]
                        gatewaySock = SocketElement(
                            self.traceProcessor.gatewayIP,
                            sourcePort,
                            record.details["saddr"],
                            record.details["sport"],
                            SocketStatus.REQUEST,
                            None,
                        )
                        networkThreadState = NetworkThreadState(
                            None,
                            self,
                            traceID,
                            gatewaySock,
                            self.tcpState.startTime,
                        )
                        # No reference to source thread as the source thread is docker gateway
                        self.addRootNetworkThreadState(
                            networkThreadState,
                            (None, traceID, self.traceProcessor.gatewayIP, sourcePort),
                        )
                        if self.traceProcessor.toPrint:
                            if self.traceProcessor.colored:
                                print(
                                    f"{bcolors.BOLD}{bcolors.BLUE}{self.container}@{record.pid}{bcolors.ENDC}{bcolors.BOLD}{bcolors.GREEN} receiving request{bcolors.ENDC} at time {record.timeStamp}{bcolors.RED} from {record.details['daddr'], record.details['dport']}{bcolors.YELLOW} to {record.details['saddr'], record.details['sport']}"
                                )
                            else:
                                print(
                                    f"{self.container}@{record.pid} receiving request at time {record.timeStamp} from {record.details['daddr'], record.details['dport']} to {record.details['saddr'], record.details['sport']}"
                                )
                    else:
                        activeNetworkThreadStateCount = 0
                        for key in self.networkThreadStates:
                            if key[0] == None:
                                activeNetworkThreadStateCount += 1

                                self.networkThreadStates[key].updateEndTime(
                                    record.timeStamp
                                )
                        if activeNetworkThreadStateCount > 1:
                            print(
                                "ERROR : More than one active network thread state in nginx thread"
                            )
                            exit()
                else:
                    sourceIP = record.details["daddr"]
                    sourcePort = record.details["dport"]
                    destinationIP = record.details["saddr"]
                    destinationPort = record.details["sport"]
                    sourceSocket = self.traceProcessor.socketPool.getSocket(
                        sourceIP, sourcePort, destinationIP, destinationPort
                    )
                    if sourceSocket:
                        sourceThread = sourceSocket.srcThread

                        isRequest = False
                        if sourceSocket.socketStatus == SocketStatus.REQUEST:
                            isRequest = True

                        if isRequest:
                            incomingRequestTraces = set()
                            if self.traceProcessor.toPrint:
                                if self.traceProcessor.colored:
                                    print(
                                        f"{bcolors.BOLD}{bcolors.BLUE}{self.container}@{record.pid}{bcolors.ENDC}{bcolors.BOLD}{bcolors.GREEN} receiving request{bcolors.ENDC} at time {record.timeStamp}{bcolors.RED} from {record.details['daddr'], record.details['dport']}{bcolors.YELLOW} to {record.details['saddr'], record.details['sport']}"
                                    )
                                else:
                                    print(
                                        f"{self.container}@{record.pid} receiving request at time {record.timeStamp} from {record.details['daddr'], record.details['dport']} to {record.details['saddr'], record.details['sport']}"
                                    )

                            for networkStateKey in sourceThread.networkThreadStates:
                                incomingRequestTraces.add(networkStateKey[1])

                            for forkState in sourceThread.forkThreadStates:
                                incomingRequestTraces.add(forkState.traceID)

                            statesToPop = list()
                            # Move existing state to permanent log from intermediate store due to it incoming request being from same source
                            for networkStateKey in self.intermediateThreadStates:
                                sourceThreadToBeChecked = networkStateKey[0]
                                sourceIPToBeChecked = networkStateKey[2]
                                sourcePortToBeChecked = networkStateKey[3]
                                netState = self.intermediateThreadStates[
                                    networkStateKey
                                ]
                                if (
                                    sourceThread == sourceThreadToBeChecked
                                    and sourceIPToBeChecked == netState.srcSocket.srcIp
                                    and sourcePortToBeChecked
                                    == netState.srcSocket.srcPort
                                    and netState.traceID in incomingRequestTraces
                                ):
                                    statesToPop.append(networkStateKey)

                            for networkStateKey in statesToPop:
                                self.networkThreadStateLog.append(
                                    self.intermediateThreadStates.pop(networkStateKey)
                                )

                            # Check if a state already exists in the current network states
                            # Logic to move into intermediate
                            statesToPop = list()
                            for networkStateKey in self.networkThreadStates:
                                sourceThreadToBeChecked = networkStateKey[0]
                                sourceIPToBeChecked = networkStateKey[2]
                                sourcePortToBeChecked = networkStateKey[3]
                                netState = self.networkThreadStates[networkStateKey]
                                if (
                                    sourceThread != sourceThreadToBeChecked
                                    or netState.traceID not in incomingRequestTraces
                                    or sourceIP != sourceIPToBeChecked
                                    or sourcePort != sourcePortToBeChecked
                                ):
                                    netState.setNewSrcObserved()
                                if (
                                    netState.isResponseSentOnce()
                                    and netState.isNewSrcObserved()
                                ):
                                    self.intermediateThreadStates[
                                        (
                                            sourceThread,
                                            netState.traceID,
                                            sourceIP,
                                            sourcePort,
                                        )
                                    ] = netState
                                    statesToPop.append(networkStateKey)

                            # Removing all the threads from activethreadstate which got moved to intermediate store
                            for networkStateKey in statesToPop:
                                self.networkThreadStates.pop(networkStateKey)

                            # Create a child state for each (network thread state in the parent)
                            try:
                                for networkStateKey in sourceThread.networkThreadStates:
                                    traceID = networkStateKey[1]
                                    key = (
                                        sourceThread,
                                        traceID,
                                        sourceIP,
                                        sourcePort,
                                    )
                                    # Checking if state already exists
                                    if key not in self.networkThreadStates:
                                        networkThreadState = NetworkThreadState(
                                            sourceThread,
                                            self,
                                            traceID,
                                            sourceSocket,
                                            self.tcpState.startTime,
                                        )

                                        self.addNetworkThreadState(
                                            networkThreadState,
                                            (
                                                sourceThread,
                                                traceID,
                                                sourceIP,
                                                sourcePort,
                                            ),
                                        )
                                    else:
                                        self.networkThreadStates[key].updateEndTime(
                                            record.timeStamp
                                        )
                            except:
                                print("TERMINATING FIRST PASS: Error with tcp_probe")
                                self.traceProcessor.terminate()
                                print(len(self.traceProcessor.traceGenesis))
                                self.traceProcessor.serializeTraceData()
                                exit()

                            # Create a child state for each (fork thread state in the parent)
                            for forkState in sourceThread.forkThreadStates:
                                forkTraceID = forkState.traceID
                                # Assuming two threads with the same parent, do not send requests over TCP between them
                                key = (
                                    sourceThread,
                                    forkTraceID,
                                    sourceIP,
                                    sourcePort,
                                )
                                if key not in self.networkThreadStates:
                                    networkThreadState = NetworkThreadState(
                                        sourceThread,
                                        self,
                                        forkTraceID,
                                        sourceSocket,
                                        self.tcpState.startTime,
                                    )

                                    self.addNetworkThreadState(
                                        networkThreadState,
                                        (
                                            sourceThread,
                                            forkTraceID,
                                            sourceIP,
                                            sourcePort,
                                        ),
                                    )
                                else:
                                    self.networkThreadStates[key].updateEndTime(
                                        record.timeStamp
                                    )
                        # receiving a response
                        else:
                            if self.traceProcessor.toPrint:
                                if self.traceProcessor.colored:
                                    print(
                                        f"{bcolors.BOLD}{bcolors.BLUE}{self.container}@{record.pid}{bcolors.ENDC}{bcolors.BOLD}{bcolors.GREEN} receiving response{bcolors.ENDC} at time {record.timeStamp}{bcolors.RED} from {record.details['daddr'], record.details['dport']}{bcolors.YELLOW} to {record.details['saddr'], record.details['sport']}"
                                    )
                                else:
                                    print(
                                        f"{self.container}@{record.pid} receiving response at time {record.timeStamp} from {record.details['daddr'], record.details['dport']} to {record.details['saddr'], record.details['sport']}"
                                    )

            elif record.event in [
                "sys_exit_recvfrom",
                "sys_exit_read",
                "sys_exit_recvmsg",
                "sys_exit_readv",
            ]:
                del self.tcpState
                self.tcpState = None
