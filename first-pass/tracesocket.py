from enum import Enum


class SocketStatus(Enum):

    UNKNOWN = 0
    REQUEST = 1
    RESPONSE = -1


class SocketElement():

    def __init__(self, srcIp: str, srcPort: int, destIp: str, destPort: int, sockCookie: int or str):
        self.srcIp: str = srcIp
        self.srcPort: int = srcPort
        self.destIp: str = destIp
        self.destPort: int = destPort
        if type(sockCookie) == int:
            self.sockCookie: int = sockCookie
        else:
            self.sockCookie: int = int(sockCookie, base=16)
        self.socketStatus = SocketStatus.UNKNOWN
        self.srcThread = None
        self.dataLen: int = None  # socket dataLen currently not used

    def setRequest(self, thread, dataLen: int = None):

        self.socketStatus = SocketStatus.REQUEST
        self.srcThread = thread
        self.dataLen = dataLen

    def setResponse(self, thread, dataLen: int = None):

        self.socketStatus = SocketStatus.RESPONSE
        self.srcThread = thread
        self.dataLen = dataLen

    def consumeData(self, dataLen: int):
        pass