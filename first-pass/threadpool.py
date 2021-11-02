from tracethread import *
from tracerecord import *
from socketpool import *


class ThreadPool():
    def __init__(self, socketPool: SocketPool):
        self.activeThreadPool = dict()  # key is PID, value is a Thread object
        self.deadThreadPool = list()  # contains Dead Thread objects
        self.socketPool = socketPool
        # Thread is dead on a sched_switch with Z or X

    def processSched(self, record: TraceRecord):
        if 'sched' in record.event:
            print(len(self.activeThreadPool))
        if record.event == 'sched_switch':
            prevThread: Thread = self.activeThreadPool.get(
                int(record.details['prev_pid']))
            nextThread: Thread = self.activeThreadPool.get(
                int(record.details['next_pid']))
            if prevThread:
                prevThread.setCurrentSchedState(
                    record.timeStamp,
                    ThreadWakeState(int(record.details["prev_state"])))
            if nextThread:
                nextThread.setCurrentSchedState(record.timeStamp,
                                                ThreadWakeState.RUNNING)
        elif record.event == 'sched_process_exit':
            dyingThread: Thread = self.getThread(record.pid)
            if dyingThread:
                # TODO verify thread state
                dyingThread.setCurrentSchedState(record.timeStamp,
                                                 ThreadWakeState.EXIT_DEAD)
                success = self.killThread(dyingThread)
                if not success:
                    print(
                        f"Thread could not be removed\nPID {record.pid} already in thread POOL"
                    )
            # else:
            # print("MAJOR ERROR, Thread in LOG AND NOT IN POOL")

        elif record.event == 'sched_process_fork':
            parentThread: Thread = self.getThread(
                int(record.details['parent_pid']))
            if parentThread:
                #TODO verify Thread Wake State
                newThread = Thread(
                    int(record.details['child_pid']), parentThread.container,
                    self, self.socketPool,
                    ThreadSchedEvent(record.timeStamp, ThreadWakeState.WAKING))
                success = self.addThread(newThread)
                if not success:
                    print(
                        f"Thread could not be added into the pool\nDuplicate PID {record.pid}"
                    )

            # else:
            #     print("MAJOR ERROR, Thread in LOG AND NOT IN POOL")

    def freeActiveThreadPool(self):
        for key in list(self.activeThreadPool.keys()):
            self.deadThreadPool.append(self.activeThreadPool.pop(key))

    def addThread(self, newThread: Thread):
        if newThread.pid not in self.activeThreadPool:
            self.activeThreadPool[newThread.pid] = newThread
            return True
        return False

    def getThread(self, pid: int):
        if pid in self.activeThreadPool:
            return self.activeThreadPool[pid]
        else:
            print(f"Thread {pid} not found in active thread pool")
            return None

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
