from core.tracerecord import TraceRecord
import json


class CustomTraceHandler:
    def __init__(self, traceId, traceProcessor):
        self.traceId = traceId
        self.traceProcessor = traceProcessor
        self.customInit()

    def retrieveData(self) -> str:
        return json.dumps(self.customRetrieveData())

    def consumeRecord(self, record: TraceRecord):
        self.customConsumeRecord(record)

    def customInit(self):
        self.c = 0

    def customConsumeRecord(self, record: TraceRecord):
        self.c += 1

    def customRetrieveData(self) -> dict:
        return {"count": self.c}
