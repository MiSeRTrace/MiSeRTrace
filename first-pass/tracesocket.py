from enum import Enum
from tracethread import Thread


class SocketStatus(Enum):
    REQUEST = 0
    RESPONSE = 1


class SocketElement():
    def __init__(self,
                 srcIp: str,
                 srcPort: int,
                 destIp: str,
                 destPort: int,
                 sockCookie: int or str,
                 socketStatus: SocketStatus,
                 srcThread: Thread,
                 dataLen: int = None):
        self.srcIp: str = srcIp
        self.srcPort: int = srcPort
        self.destIp: str = destIp
        self.destPort: int = destPort
        if type(sockCookie) == int:
            self.sockCookie: int = sockCookie
        else:
            self.sockCookie: int = int(sockCookie, base=16)
        self.socketStatus: SocketStatus = socketStatus
        self.srcThread: Thread = srcThread
        self.dataLen: int = dataLen
