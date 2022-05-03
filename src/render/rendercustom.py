from io import TextIOWrapper
from render.renderinterface import RenderInterface
from render.customrenders.customthreadstatehandler import CustomThreadStateHandler
from render.customrenders.customtracehandler import CustomTraceHandler
from core.threadstate import ForkThreadState, NetworkThreadState
from core.tracerecord import TraceRecord
import json
import csv
from tqdm import tqdm


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


class RenderCustom(RenderInterface):
    def __init__(self, fileObject: TextIOWrapper, **argv):
        super().__init__(fileObject)
        if argv["args"].range:
            self.rangeSet = self.getRangeSet(argv["args"].range)
        else:
            self.rangeSet = set(i for i in range(1, self.traceProcessor.traceID + 1))
        self.outputFile = argv["outputFile"]

    def getRangeSet(self, rangeStr: str):
        rangeSet = set()
        for elem in rangeStr.strip().split(","):
            if "-" in elem:
                continuousRange = elem.split("-")
                rangeSet.update(
                    set(
                        i
                        for i in range(
                            int(continuousRange[0]), int(continuousRange[1]) + 1
                        )
                    )
                )
            else:
                rangeSet.add(int(elem))
        return rangeSet

    def serializeTraceData(self):
        traceData = dict()
        recordHandlers = set()
        for traceId in self.rangeSet:
            threadStateObject = self.traceProcessor.traceGenesis[traceId]
            customTraceHandler = CustomTraceHandler(traceId, self.traceProcessor)
            customThreadStateHandler = CustomThreadStateHandler(
                traceId, threadStateObject, self.traceProcessor, customTraceHandler
            )
            traceData[traceId] = {
                "ThreadState": threadStateObject,
                "ThreadHandler": customThreadStateHandler,
                "TraceHandler": customTraceHandler,
                "Children": list(),
            }
            recordHandlers.add(customThreadStateHandler)
            if traceId in threadStateObject.handlingThread.destinationThreadStates:
                self._recursiveFillTraceData(
                    traceId,
                    self.traceProcessor,
                    threadStateObject.startTimeStamp,
                    threadStateObject.handlingThread.destinationThreadStates,
                    traceData[traceId]["Children"],
                    customTraceHandler,
                    recordHandlers,
                    set(),
                )
        return traceData, recordHandlers

    def _recursiveFillTraceData(
        self,
        traceId: int,
        traceProcessor,
        parentStateStartTimeStamp: float,
        destinationThreadStates: "dict[int, list[NetworkThreadState or ForkThreadState]]",
        container: list,
        customTraceHandler: CustomTraceHandler,
        recordHandlers: set,
        visited: set,
    ):
        for threadStateObject in destinationThreadStates[traceId][::-1]:
            if (
                threadStateObject not in visited
                and threadStateObject.startTimeStamp >= parentStateStartTimeStamp
            ):
                visited.add(threadStateObject)
                customThreadStateHandler = CustomThreadStateHandler(
                    traceId, threadStateObject, traceProcessor, customTraceHandler
                )
                recordHandlers.add(customThreadStateHandler)
                element = {
                    "ThreadState": threadStateObject,
                    "ThreadHandler": customThreadStateHandler,
                    "Children": list(),
                }
                container.insert(0, element)

                if traceId in threadStateObject.handlingThread.destinationThreadStates:
                    self._recursiveFillTraceData(
                        traceId,
                        traceProcessor,
                        threadStateObject.startTimeStamp,
                        threadStateObject.handlingThread.destinationThreadStates,
                        element["Children"],
                        customTraceHandler,
                        recordHandlers,
                        visited,
                    )

    def render(self, **argv):
        traceData, recordHandlers = self.serializeTraceData()
        fp = open(argv["args"].tracelogs, "r")
        traceCsv = csv.reader(fp, delimiter="|")
        for line in tqdm(
            traceCsv,
            desc="PROCESSING",
            unit="line",
            total=self.traceProcessor.recordsProcessed,
        ):
            record = TraceRecord(line)
            popSet = set()
            for handler in recordHandlers:
                if not handler.consumeRecord(record):
                    popSet.add(handler)
            recordHandlers -= popSet
        if argv["args"].r:
            if argv["args"].f:
                print(
                    json.dumps(self.serializeOutput(traceData), indent=4),
                    file=self.outputFile,
                )
            else:
                print(json.dumps(self.serializeOutput(traceData)), file=self.outputFile)
        else:
            self.printData(self.serializeOutput(traceData), argv["args"].c)

    def _recursiveSerializeOutput(self, traceData, outputData):
        for span in traceData:
            threadStateObject = span["ThreadState"]
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
                "ThreadOutput": span["ThreadHandler"].retrieveData(),
                "Children": list(),
            }
            outputData.append(element)
            self._recursiveSerializeOutput(span["Children"], element["Children"])

    def serializeOutput(self, traceData):
        outputData = dict()
        for traceId in traceData:
            threadStateObject = traceData[traceId]["ThreadState"]
            outputValue = {
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
                "TraceOutput": traceData[traceId]["TraceHandler"].retrieveData(),
                "ThreadOutput": traceData[traceId]["ThreadHandler"].retrieveData(),
                "Children": [],
            }
            outputData[traceId] = outputValue
            self._recursiveSerializeOutput(
                traceData[traceId]["Children"], outputValue["Children"]
            )
        return outputData

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
                    bcolors.PINK + "::" + bcolors.ENDC,
                    "TraceOutput",
                    bcolors.PINK + "-->" + bcolors.ENDC,
                    json.dumps(traceDetails["TraceOutput"]),
                    "ThreadOutput",
                    bcolors.PINK + "-->" + bcolors.ENDC,
                    json.dumps(traceDetails["ThreadOutput"]),
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
                    "::",
                    "TraceOutput",
                    "-->",
                    json.dumps(traceDetails["TraceOutput"]),
                    "ThreadOutput",
                    "-->",
                    json.dumps(traceDetails["ThreadOutput"]),
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
                    bcolors.PINK + "::" + bcolors.ENDC,
                    "ThreadOutput",
                    bcolors.PINK + "-->" + bcolors.ENDC,
                    json.dumps(span["ThreadOutput"]),
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
                    "::",
                    "ThreadOutput",
                    "-->",
                    json.dumps(span["ThreadOutput"]),
                    file=self.outputFile,
                )
            self.recPrintData(span["Children"], colored, depth + 1)
