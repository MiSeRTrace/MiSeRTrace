from tracethread import *


class ThreadPool():

    def __init__(self):
        self.activeThreadPool = dict()  # key is PID, value is a Thread object
        self.deadThreadPool = list()  # contains Dead Thread objects
        # Thread is dead on a sched_switch with Z or X

    def freeActiveThreadPool(self):
        for key in list(self.activeThreadPool.keys()):
            self.deadThreadPool.append(self.activeThreadPool.pop(key))

    def addThread(self, newThread: Thread):
        if newThread.pid not in self.activeThreadPool:
            self.activeThreadPool[newThread.pid] = newThread
            return True
        return False

    def killThread(self, killThread: Thread):
        if killThread.pid in self.activeThreadPool:
            self.deadThreadPool.append(
                self.activeThreadPool.pop(killThread.pid))
            return True
        return False

    def killPid(self, killPid: int):
        if killPid in self.activeThreadPool:
            self.deadThreadPool.append(self.activeThreadPool.pop(killPid))
            return True
        return False
