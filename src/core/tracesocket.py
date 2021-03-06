from enum import Enum


class SocketStatus(Enum):
    REQUEST = 0
    RESPONSE = 1


class SocketElement:
    def __init__(
        self,
        srcIp: str,
        srcPort: str,
        destIp: str,
        destPort: str,
        socketStatus: SocketStatus,
        srcThread,
        sockCookie: str = None,
        dataLen: int = None,
    ):
        self.srcIp: str = srcIp
        self.srcPort: str = srcPort
        self.destIp: str = destIp
        self.destPort: str = destPort
        self.socketStatus: SocketStatus = socketStatus
        self.srcThread = srcThread
        self.sockCookie: str = sockCookie
        self.dataLen: int = dataLen
