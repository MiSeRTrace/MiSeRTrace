from tracesocketpool import *
from tracethreadpool import *
from tracerecord import *
from globalstatemanager import GlobalStateManager

class TraceProcessor():

    def __init__(self,gsClasses:list):
        self.threadPool: ThreadPool = ThreadPool()
        self.socketPool: SocketPool = SocketPool()
        self.globalStateManager:GlobalStateManager = GlobalStateManager(gsClasses=gsClasses)
        self.previousTimeStamp: float = 0.0

    

    def _validRecord(self, record: TraceRecord): # basic validation checks can be added here
        # ensures that the records are inserted in non-decreasing order of time
        if self.previousTimeStamp <= record.timeStamp:
            self.previousTimeStamp = record.timeStamp
            return True
        return False

    def consumeRecord(self, record: TraceRecord):
        if not self._validRecord(record):
            return False   
