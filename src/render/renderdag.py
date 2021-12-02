from io import TextIOWrapper
from render.renderinterface import RenderInterface
from core.threadstate import ForkThreadState, NetworkThreadState


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


class RenderDag(RenderInterface):
    def __init__(self, fileObject: TextIOWrapper):
        super().__init__(fileObject)

    def render(self, **argv):
        serializedData = self.serializeTraceData()
        if argv["args"].R:
            print(serializedData)
        else:
            self.printData(serializedData, argv["args"].C)

    def serializeTraceData(self):
        traceData: dict[tuple, dict] = dict()

        for traceId in self.traceProcessor.traceGenesis:
            threadStateObject = self.traceProcessor.traceGenesis[traceId]
            traceData[
                (
                    traceId,
                    threadStateObject.handlingThread.pid,
                    threadStateObject.handlingThread.container,
                    threadStateObject.handlingThread.ip,
                    threadStateObject.startTimeStamp,
                    threadStateObject.endTimeStamp,
                )
            ] = dict()

            if traceId in threadStateObject.handlingThread.destinationThreadStates:
                self._recursiveFillTraceData(
                    traceId,
                    threadStateObject.startTimeStamp,
                    threadStateObject.handlingThread.destinationThreadStates,
                    traceData[
                        (
                            traceId,
                            threadStateObject.handlingThread.pid,
                            threadStateObject.handlingThread.container,
                            threadStateObject.handlingThread.ip,
                            threadStateObject.startTimeStamp,
                            threadStateObject.endTimeStamp,
                        )
                    ],
                )
        return traceData

    def _recursiveFillTraceData(
        self,
        traceId: int,
        parentStateStartTimeStamp: float,
        destinationThreadStates: "dict[int, list[NetworkThreadState or ForkThreadState]]",
        container: "dict[tuple, dict]",
    ):
        for threadStateObject in destinationThreadStates[traceId]:
            if threadStateObject.startTimeStamp >= parentStateStartTimeStamp:
                if type(threadStateObject) == ForkThreadState:
                    state = "ForkThreadState"
                else:
                    state = "NetworkThreadState"

                container[
                    (
                        state,
                        threadStateObject.handlingThread.pid,
                        threadStateObject.handlingThread.container,
                        threadStateObject.handlingThread.ip,
                        threadStateObject.startTimeStamp,
                        threadStateObject.endTimeStamp,
                    )
                ] = dict()
                if traceId in threadStateObject.handlingThread.destinationThreadStates:

                    self._recursiveFillTraceData(
                        traceId,
                        threadStateObject.startTimeStamp,
                        threadStateObject.handlingThread.destinationThreadStates,
                        container[
                            (
                                state,
                                threadStateObject.handlingThread.pid,
                                threadStateObject.handlingThread.container,
                                threadStateObject.handlingThread.ip,
                                threadStateObject.startTimeStamp,
                                threadStateObject.endTimeStamp,
                            )
                        ],
                    )

    def recPrintData(self, traceElem, colored: bool, depth: int):
        for span in traceElem:
            if colored:
                print(
                    depth * "\t",
                    bcolors.BOLD,
                    bcolors.PINK,
                    bcolors.BOLD + bcolors.YELLOW + span[0] + bcolors.ENDC,
                    bcolors.BOLD,
                    bcolors.BLUE,
                    span[2],
                    bcolors.ENDC,
                    "at time",
                    bcolors.GREEN,
                    span[4],
                    bcolors.ENDC,
                    "to",
                    bcolors.RED,
                    span[5],
                )
            else:
                print(
                    depth * "\t",
                    span[0],
                    span[2],
                    "at time",
                    span[4],
                    "to",
                    span[5],
                )
            self.recPrintData(traceElem[span], colored, depth + 1)

    def printData(self, serializedData, colored: bool):
        for trace in serializedData:
            if colored:
                print(
                    bcolors.PINK,
                    trace[0],
                    bcolors.BLUE,
                    bcolors.BOLD,
                    trace[2],
                    "at time",
                    bcolors.GREEN,
                    trace[4],
                    "to",
                    bcolors.RED,
                    trace[5],
                )
            else:
                print(
                    trace[0],
                    trace[2],
                    "at time",
                    trace[4],
                    "to",
                    trace[5],
                )
            self.recPrintData(serializedData[trace], colored, 1)
