from enum import Enum
from tracethread import Thread


class SocketStatus(Enum):
    REQUEST = 0
    RESPONSE = 1


class SocketElement():
    def __init__(self,
                 srcIp: str,
                 srcPort: str,
                 destIp: str,
                 destPort: str,
                 sockCookie: str,
                 socketStatus: SocketStatus,
                 srcThread: Thread,
                 dataLen: int = None):
        self.srcIp: str = srcIp
        self.srcPort: str = srcPort
        self.destIp: str = destIp
        self.destPort: str = destPort
        self.sockCookie: str = sockCookie
        self.socketStatus: SocketStatus = socketStatus
        self.srcThread: Thread = srcThread
        self.dataLen: int = dataLen
