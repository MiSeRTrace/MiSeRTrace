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


class SocketPool():

    def __init__(self):

        # key is a tuple of srcIp, srcPort,sock_cookie
        self.activeSocketPool: dict[tuple, SocketElement] = dict()
        # append only, objects inside are immutable
        self.destroyedSocketPool: list[SocketElement] = list()

    def addSocket(self, socketElement: SocketElement):
        key = (socketElement.srcIp, socketElement.srcPort,
               socketElement.sockCookie)
        if key not in self.activeSocketPool:
            self.activeSocketPool[key] = socketElement
            return True
        return False

    def getActiveSocket(self, srcIp: str, srcPort: int, sockCookie: int):
        key = (srcIp, srcPort, sockCookie)
        return self.activeSocketPool.get(key)

    def destroyActiveSocket(self, srcIp: str, srcPort: int, sockCookie: int):
        key = (srcIp, srcPort, sockCookie)
        if key in self.activeSocketPool:
            self.destroyedSocketPool.append(self.activeSocketPool.pop(key))
            return True
        return False