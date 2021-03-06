from core.tracethread import *


class ThreadPool:
    def __init__(self, traceProcessor):
        self.activeThreadPool = dict()  # key is PID, value is a Thread object
        self.deadThreadPool = list()  # contains Dead Thread objects
        self.traceProcessor = traceProcessor

    def processSchedEvents(self, record: TraceRecord):
        # print(len(self.activeThreadPool))

        # sched_process_exit: Event observed when a thread dies
        if record.isImplementation:
            if record.event == "sched_process_exit":
                dyingThread: Thread = self.getThread(record.pid)
                if dyingThread:
                    for forkState in dyingThread.forkThreadStates:
                        forkState.updateEndTime(record.timeStamp)
                    # EXIT_DEAD occurs once, on redis-server
                    self.killThread(dyingThread)
                else:
                    print(
                        f"WARNING: Thread {record.pid} not in active pool, cannot be moved to dead pool"
                    )
                    # exit()

            # sched_process_fork: Event observed when a thread forks
            elif record.event == "sched_process_fork":
                parentThread: Thread = self.getThread(int(record.details["parent_pid"]))
                # print(parentThread)
                # print(record.timeStamp)
                if parentThread:
                    newThread = Thread(
                        int(record.details["child_pid"]),
                        parentThread.container,
                        parentThread.ip,
                        self.traceProcessor,
                    )
                    # print(newThread.container)
                    # print(record.timeStamp)
                    if not self.addThread(newThread):
                        print(
                            f"ERROR: Thread could not be added into the pool\nDuplicate PID {record.details['child_pid']}"
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
                        forkThreadState = ForkThreadState(
                            parentThread, newThread, parentTraceID, record.timeStamp
                        )
                        newThread.addForkThreadState(forkThreadState)
                    for key in parentThread.networkThreadStates:
                        parentTraceID = key[1]
                        forkThreadState = ForkThreadState(
                            parentThread, newThread, parentTraceID, record.timeStamp
                        )
                        newThread.addForkThreadState(forkThreadState)
                    # for object in newThread.forkThreadStates:
                    #     print(
                    #         newThread.pid, "->", object.srcThread, object.traceID, "DUMMY"
                    # )
                    # print(
                    #     "DUMMY Is new source observed:",
                    #     self.networkThreadStates[key].isNewSrcObserved(),
                    # )
                    # print(
                    #     "DUMMY Is response sent once:",
                    #     self.networkThreadStates[key].isResponseSentOnce(),
                    # )
                else:
                    print(
                        "WARNING: Parent thread not in active thread pool while forking"
                    )
                    # exit()

    def freeActiveThreadPool(self):
        for key in list(self.activeThreadPool):
            self.killThread(self.activeThreadPool[key])

    def addThread(self, newThread: Thread):
        if newThread.pid not in self.activeThreadPool:
            self.activeThreadPool[newThread.pid] = newThread
            return True
        return False

    def getThread(self, pid: int):
        return self.activeThreadPool.get(pid)

    def killThread(self, thread: Thread):
        if thread.pid in self.activeThreadPool:
            for forkState in thread.forkThreadStates:
                forkState.updateEndTime(self.traceProcessor.lastTimeStamp)
            for key in list(thread.networkThreadStates):
                thread.networkThreadStateLog.append(thread.networkThreadStates.pop(key))
            for key in list(thread.intermediateThreadStates):
                thread.networkThreadStateLog.append(
                    thread.intermediateThreadStates.pop(key)
                )
            self.deadThreadPool.append(self.activeThreadPool.pop(thread.pid))
            return True
        return False
