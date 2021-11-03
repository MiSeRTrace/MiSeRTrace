from tracesocket import *


class SocketPool():
    def __init__(self):
        # key is a tuple of srcIp, srcPort,destIp, destPort
        self.socketPool: dict[tuple, SocketElement] = dict()

    def addSocket(self, socketElement: SocketElement):
        key = (socketElement.srcIp, socketElement.srcPort,
               socketElement.destIp, socketElement.destPort)
        if key not in self.socketPool:
            self.socketPool[key] = socketElement
            return True
        return False

    def getSocket(self, srcIp: str, srcPort: int, destIp: str, destPort: int):
        key = (srcIp, srcPort, destIp, destPort)
        return self.socketPool.get(key)

    def deleteSocket(self, srcIp: str, srcPort: int, destIp: str,
                     destPort: int):
        key = (srcIp, srcPort, destIp, destPort)
        if key in self.socketPool:
            self.socketPool.pop(key)
            return True
        return False
