from core.tracerecord import TraceRecord
from core.threadstate import ForkThreadState, NetworkThreadState
from core.traceprocessor import TraceProcessor
from .customtracehandler import CustomTraceHandler
import json


class CustomThreadStateRender:
    def __init__(self, traceId, threadState, traceProcessor, customTraceHandler):
        self.traceId: int = traceId
        self.threadState: NetworkThreadState or ForkThreadState = threadState
        self.traceProcessor: TraceProcessor = traceProcessor
        self.traceHandler: CustomTraceHandler = customTraceHandler
        self.customInit()

    def consumeRecord(self, record: TraceRecord):
        if (
            self.threadState.handlingThread.pid == record.pid
            and self.threadState.startTimeStamp <= record.timeStamp
            and self.threadState.endTimeStamp >= record.timeStamp
        ):
            self.traceHandler.consumeRecord(record)
            self.customConsumeRecord(record)

    def retrieveData(self) -> str:
        return json.dumps(self.customRetrieveData())

    def customInit(self):
        self.c = 0

    def customConsumeRecord(self, record: TraceRecord):
        self.c += 1

    def customRetrieveData(self) -> dict:
        return {"count": self.c}
