from tracesocket import *


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
