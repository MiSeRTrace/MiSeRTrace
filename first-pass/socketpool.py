from tracesocket import *
from tracethread import Thread


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

    def updateSocket(self, socketElement: SocketElement,
                     socketStatus: SocketStatus, srcThread: Thread):
        key = (socketElement.srcIp, socketElement.srcPort,
               socketElement.destIp, socketElement.destPort)
        if key in self.socketPool:
            self.socketPool[key].socketStatus = socketStatus
            self.socketPool[key].srcThread = srcThread
            return True
        return False

    def getSocket(self, srcIp: str, srcPort: str, destIp: str, destPort: str):
        key = (srcIp, srcPort, destIp, destPort)
        return self.socketPool.get(key)

    def deleteSocket(self, socketElement: SocketElement):
        key = (socketElement.srcIp, socketElement.srcPort,
               socketElement.destIp, socketElement.destPort)
        if key in self.socketPool:
            self.socketPool.pop(key)
            return True
        return False
