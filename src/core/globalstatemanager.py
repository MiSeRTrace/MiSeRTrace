from core.tracerecord import TraceRecord


class GlobalStateInterface:

    ID: str

    def consumeRecord(self, record: TraceRecord):
        pass

    def retrieveData(self):
        pass


class GlobalStateManager:
    def __init__(self, gsClasses: list):
        self.GlobalStateStore: dict[str, GlobalStateInterface] = dict()
        for cls in gsClasses:
            self.GlobalStateStore[cls.ID] = cls()

    def consumeRecord(self, record: TraceRecord):
        for object in self.GlobalStateStore:
            object.consumeRecord(record)

    def retrieveAllData(self):
        return {
            self.GlobalStateStore[id]: self.GlobalStateStore[id].retrieveData()
            for object in self.GlobalStateStore
        }

    def retrieveData(self, id: str):
        if id in self.GlobalStateStore:
            return self.GlobalStateStore[id].retrieveData()
        return None
