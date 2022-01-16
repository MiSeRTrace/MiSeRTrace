from io import TextIOWrapper
from render.renderinterface import RenderInterface
from render.rendercustomhandler.customthreadstaterender import CustomThreadStateRender
from render.rendercustomhandler.customtracehandler import CustomTraceHandler
from core.threadstate import ForkThreadState, NetworkThreadState
from core.tracerecord import TraceRecord


class RenderCustom(RenderInterface):
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
        traceData: dict[tuple, dict] = dict()
        recordHandlers = set()
        for traceId in self.rangeSet:
            threadStateObject = self.traceProcessor.traceGenesis[traceId]
            customTraceHandler = CustomTraceHandler(traceId, self.traceProcessor)
            customThreadStateHandler = CustomThreadStateRender(
                traceId, threadStateObject, self.traceProcessor, customTraceHandler
            )
            traceData[(traceId, threadStateObject)] = (
                dict(),
                customThreadStateHandler,
                customTraceHandler,
            )
            recordHandlers.add(customThreadStateHandler)
            if traceId in threadStateObject.handlingThread.destinationThreadStates:
                self._recursiveFillTraceData(
                    traceId,
                    self.traceProcessor,
                    threadStateObject.startTimeStamp,
                    threadStateObject.handlingThread.destinationThreadStates,
                    traceData[(traceId, threadStateObject)],
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
        container: "dict[tuple, tuple]",
        customTraceHandler: CustomTraceHandler,
        recordHandlers: set,
        visited: set,
    ):
        tempContainerList: list = list()
        for threadStateObject in destinationThreadStates[traceId][::-1]:
            if (
                threadStateObject not in visited
                and threadStateObject.startTimeStamp >= parentStateStartTimeStamp
            ):
                visited.add(threadStateObject)
                customThreadStateHandler = CustomThreadStateRender(
                    traceId, threadStateObject, traceProcessor, customTraceHandler
                )
                recordHandlers.add(customThreadStateHandler)
                element = (threadStateObject, (dict(), customThreadStateHandler))
                tempContainerList.insert(0, element)

                if traceId in threadStateObject.handlingThread.destinationThreadStates:
                    self._recursiveFillTraceData(
                        traceId,
                        traceProcessor,
                        threadStateObject.startTimeStamp,
                        threadStateObject.handlingThread.destinationThreadStates,
                        element[1],
                        customTraceHandler,
                        recordHandlers,
                        visited,
                    )
        for element in tempContainerList:
            container[0][element[0]] = element[1]

    def __init__(self, fileObject: TextIOWrapper, **argv):
        super().__init__(fileObject)
        self.rangeSet = self.getRangeSet(argv["args"].range)

    def render(self, **argv):
        print(self.rangeSet)
        traceData, recordHandlers = self.serializeTraceData()
        fp = open(argv["args"].trace, "r")
        c = 0
        for line in fp:
            c += 1
            record = TraceRecord(line)
            for handler in recordHandlers:
                handler.consumeRecord(record)
        print(self.serializeOutput(traceData))

    def _recursiveSerializeOutput(self, traceData, outputData):
        for key in traceData:
            value = traceData[key]
            if type(key) == ForkThreadState:
                state = "ForkThreadState"
            else:
                state = "NetworkThreadState"
            outputKey = (
                state,
                key.handlingThread.pid,
                key.handlingThread.container,
                key.handlingThread.ip,
                key.startTimeStamp,
                key.endTimeStamp,
                value[1].retrieveData(),
            )
            outputData[outputKey] = dict()
            self._recursiveSerializeOutput(value[0], outputData[outputKey])

    def serializeOutput(self, traceData):
        outputData = dict()
        for key in traceData:
            value = traceData[key]
            outputKey = (
                key[0],
                key[1].handlingThread.pid,
                key[1].handlingThread.container,
                key[1].handlingThread.ip,
                key[1].startTimeStamp,
                key[1].endTimeStamp,
                value[1].retrieveData(),
                value[2].retrieveData(),
            )
            outputData[outputKey] = dict()
            self._recursiveSerializeOutput(value[0], outputData[outputKey])
        return outputData
