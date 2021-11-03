from tracethread import *
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

        # sched_switch event: Changes the wake state of a thread
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
        # sched_process_exit: Event observed when a thread dies
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
        # sched_process_fork: Event observed when a thread forks
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

                # Create forkThreadState on the child thread

                # Getting a source of the parent
                # Typically there is only one state maintained in the parent thread
                # ASSUMPTION: Cases of multiple states occour only in leaf containers
                # A key (i.e. a source-tuple) is picked and the same TraceID is propagated
                # If the parent does not belong to any trace, None will be the trace of the child thread
                """
                Cases to be handled:
                    Simultaneous network and fork states in a thread
                    Multiple active states (network/fork) before fork
                    A(has network and fork states) forks B(which gets states from A and gets its own states) 
                        which inturn forks C(which gets states from both A and B)


                    Threads which do not have states belonging to a trace will not propagate
                    a traceless state to the child
                    For example, Root thread A(does not service requests) forks B
                    B will not have a fork state with respect to A
                    This is to ensure useless fork states are not propagated further
                    If B receives a request, the trace of that request will be propagated upon the fork of B to C
                """

                for parentForkState in parentThread.forkThreadState:
                    parentTraceID = parentForkState.traceID
                    forkThreadState = ForkThreadState(parentThread, newThread,
                                                      parentTraceID,
                                                      record.timeStamp)
                    newThread.addForkThreadState(forkThreadState)
                for parentNetworkState in parentThread.networkThreadStates:
                    parentTraceID = parentNetworkState.traceID
                    forkThreadState = ForkThreadState(parentThread, newThread,
                                                      parentTraceID,
                                                      record.timeStamp)
                    newThread.addForkThreadState(forkThreadState)

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
