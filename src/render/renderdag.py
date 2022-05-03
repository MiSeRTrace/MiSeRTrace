from io import TextIOWrapper
from render.renderinterface import RenderInterface
from core.threadstate import ForkThreadState, NetworkThreadState
import json


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
    def __init__(self, fileObject: TextIOWrapper, **argv):
        super().__init__(fileObject)
        self.outputFile = argv["outputFile"]

    def render(self, **argv):
        serializedData = self.serializeTraceData()
        if argv["args"].r:
            if argv["args"].f:
                print(json.dumps(serializedData, indent=4), file=self.outputFile)
            else:
                print(json.dumps(serializedData), file=self.outputFile)
        else:
            self.printData(serializedData, argv["args"].c)

    def serializeTraceData(self):
        traceData = dict()

        for traceId in self.traceProcessor.traceGenesis:
            threadStateObject = self.traceProcessor.traceGenesis[traceId]
            traceData[traceId] = {
                "TraceID": traceId,
                "ThreadState": {
                    "State": "ForkThreadState"
                    if type(threadStateObject) == ForkThreadState
                    else "NetworkThreadState",
                    "PID": threadStateObject.handlingThread.pid,
                    "Container": threadStateObject.handlingThread.container,
                    "IP": threadStateObject.handlingThread.ip,
                    "StartTime": threadStateObject.startTimeStamp,
                    "EndTime": threadStateObject.endTimeStamp,
                },
                "Children": list(),
            }

            if traceId in threadStateObject.handlingThread.destinationThreadStates:
                self._recursiveFillTraceData(
                    traceId,
                    threadStateObject.startTimeStamp,
                    threadStateObject.handlingThread.destinationThreadStates,
                    traceData[traceId]["Children"],
                    set(),
                )
        return traceData

    def _recursiveFillTraceData(
        self,
        traceId: int,
        parentStateStartTimeStamp: float,
        destinationThreadStates: "dict[int, list[NetworkThreadState or ForkThreadState]]",
        container: list,
        visited: set,
    ):
        for threadStateObject in destinationThreadStates[traceId][::-1]:
            if (
                threadStateObject not in visited
                and threadStateObject.startTimeStamp >= parentStateStartTimeStamp
            ):
                visited.add(threadStateObject)
                element = {
                    "ThreadState": {
                        "State": "ForkThreadState"
                        if type(threadStateObject) == ForkThreadState
                        else "NetworkThreadState",
                        "PID": threadStateObject.handlingThread.pid,
                        "Container": threadStateObject.handlingThread.container,
                        "IP": threadStateObject.handlingThread.ip,
                        "StartTime": threadStateObject.startTimeStamp,
                        "EndTime": threadStateObject.endTimeStamp,
                    },
                    "Children": list(),
                }
                container.insert(0, element)
                if traceId in threadStateObject.handlingThread.destinationThreadStates:
                    self._recursiveFillTraceData(
                        traceId,
                        threadStateObject.startTimeStamp,
                        threadStateObject.handlingThread.destinationThreadStates,
                        element["Children"],
                        visited,
                    )

    def printData(self, serializedData, colored: bool):
        for _, traceDetails in serializedData.items():
            if colored:
                print(
                    bcolors.PINK,
                    traceDetails["TraceID"],
                    bcolors.BLUE,
                    bcolors.BOLD,
                    traceDetails["ThreadState"]["Container"],
                    bcolors.ENDC,
                    "with PID",
                    bcolors.CYAN,
                    traceDetails["ThreadState"]["PID"],
                    bcolors.ENDC,
                    "at time",
                    bcolors.GREEN,
                    traceDetails["ThreadState"]["StartTime"],
                    "for",
                    bcolors.RED,
                    traceDetails["ThreadState"]["EndTime"]
                    - traceDetails["ThreadState"]["StartTime"],
                    file=self.outputFile,
                )
            else:
                print(
                    traceDetails["TraceID"],
                    traceDetails["ThreadState"]["Container"],
                    "with PID",
                    traceDetails["ThreadState"]["PID"],
                    "at time",
                    traceDetails["ThreadState"]["StartTime"],
                    "for",
                    traceDetails["ThreadState"]["EndTime"]
                    - traceDetails["ThreadState"]["StartTime"],
                    file=self.outputFile,
                )
            self.recPrintData(traceDetails["Children"], colored, 1)

    def recPrintData(self, traceElem, colored: bool, depth: int):
        for span in traceElem:
            if colored:
                print(
                    depth * "\t",
                    bcolors.BOLD,
                    bcolors.PINK,
                    bcolors.BOLD
                    + bcolors.YELLOW
                    + span["ThreadState"]["State"]
                    + bcolors.ENDC,
                    bcolors.BOLD,
                    bcolors.BLUE,
                    span["ThreadState"]["Container"],
                    bcolors.ENDC,
                    "with PID",
                    bcolors.CYAN,
                    span["ThreadState"]["PID"],
                    bcolors.ENDC,
                    "at time",
                    bcolors.GREEN,
                    span["ThreadState"]["StartTime"],
                    bcolors.ENDC,
                    "for",
                    bcolors.RED,
                    span["ThreadState"]["EndTime"] - span["ThreadState"]["StartTime"],
                    file=self.outputFile,
                )
            else:
                print(
                    depth * "\t",
                    span["ThreadState"]["State"],
                    span["ThreadState"]["Container"],
                    "with PID",
                    span["ThreadState"]["PID"],
                    "at time",
                    span["ThreadState"]["StartTime"],
                    "for",
                    span["ThreadState"]["EndTime"] - span["ThreadState"]["StartTime"],
                    file=self.outputFile,
                )
            self.recPrintData(span["Children"], colored, depth + 1)
