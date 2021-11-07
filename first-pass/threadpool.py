from tracethread import *
"""
TODO
# Thread is dead on a sched_switch with Z or X
Threads which do not have states belonging to a trace will not propagate
a traceless state to the child
For example, Root thread A(does not service requests) forks B
B will not have a fork state with respect to A
This is to ensure useless fork states are not propagated further
If B receives a request, the trace of that request will be propagated upon the fork of B to C
"""


class ThreadPool():
    def __init__(self, traceProcessor: TraceProcessor):
        self.activeThreadPool = dict()  # key is PID, value is a Thread object
        self.deadThreadPool = list()  # contains Dead Thread objects
        self.traceProcessor = traceProcessor

    def processSchedEvents(self, record: TraceRecord):
        #print(len(self.activeThreadPool))

        # sched_switch event: Changes the wake state of a thread
        if record.event == 'sched_switch':
            prevThread: Thread = self.getThread(int(
                record.details['prev_pid']))
            nextThread: Thread = self.getThread(int(
                record.details['next_pid']))
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
                dyingThread.setCurrentSchedState(record.timeStamp,
                                                 ThreadWakeState.EXIT_ZOMBIE)
                self.killThread(dyingThread)
            else:
                print(
                    f"Thread {record.pid} not in active pool, cannot be moved to dead pool"
                )
                exit()

        # sched_process_fork: Event observed when a thread forks
        elif record.event == 'sched_process_fork':
            parentThread: Thread = self.getThread(
                int(record.details['parent_pid']))
            if parentThread:
                newThread = Thread(
                    int(record.details['child_pid']), parentThread.container,
                    self.traceProcessor,
                    ThreadSchedState(record.timeStamp, ThreadWakeState.WAKING))
                if not self.addThread(newThread):
                    print(
                        f"Thread could not be added into the pool\nDuplicate PID {record.details['child_pid']}"
                    )
                    exit()
                """
                Create forkThreadStates in the child thread

                Cases handled:
                    Simple:
                    Typically there is only one state maintained in the parent thread
                    Cases of multiple states occur only in leaf containers

                    Complex:
                    Simultaneous network and fork states in a thread
                    Multiple active states (network/fork) before fork
                    A(has network and fork states) forks B(which gets states from A and gets its own states) 
                        which inturn forks C(which gets states from both A and B)
                """
                for parentForkState in parentThread.forkThreadStates:
                    parentTraceID = parentForkState.traceID
                    forkThreadState = ForkThreadState(parentThread, newThread,
                                                      parentTraceID,
                                                      record.timeStamp)
                    newThread.addForkThreadState(forkThreadState)
                for key in parentThread.networkThreadStates:
                    parentTraceID = key[1]
                    forkThreadState = ForkThreadState(parentThread, newThread,
                                                      parentTraceID,
                                                      record.timeStamp)
                    newThread.addForkThreadState(forkThreadState)
            else:
                print("Parent thread not in active thread pool while forking")
                exit()

    def freeActiveThreadPool(self):
        for key in self.activeThreadPool:
            self.deadThreadPool.append(self.activeThreadPool.pop(key))

    def addThread(self, newThread: Thread):
        if newThread.pid not in self.activeThreadPool:
            self.activeThreadPool[newThread.pid] = newThread
            return True
        return False

    def getThread(self, pid: int):
        return self.activeThreadPool.get(pid)

    def killThread(self, thread: Thread):
        if thread.pid in self.activeThreadPool:
            self.deadThreadPool.append(self.activeThreadPool.pop(thread.pid))
            return True
        return False