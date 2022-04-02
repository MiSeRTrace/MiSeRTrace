from cgi import parse_header


class TraceRecord:
    def __init__(self, lineContents: list, tracingBackend: str):
        try:
            # "comm"|"100"|"9999999999999"|"0"|"tracepoint:sched:sched_process_fork parent_pid=100 child_pid=101"
            if tracingBackend == "bpftrace":
                self.command = lineContents[0]
                self.pid = int(lineContents[1])
                self.timeStamp = int(lineContents[2])
                self.cpu = int(lineContents[3])
                self.probe = lineContents[4].split(":")
                if self.probe[0] == "MT":
                    self.isImplementation = True
                    self.event = self.probe[-1]
                    self.details = dict()
                    if len(lineContents) > 5:
                        for content in lineContents[5].strip().split():
                            attribute, value = content.split("=")
                            self.details[attribute] = value
                else:
                    self.isImplementation = False
                self.content = lineContents
            # kworker/1:0-17144 [001]  7510.995838: sched_switch:          prev_comm=kworker/1:0 prev_pid=17144 prev_prio=120 prev_state=128 next_comm=ksoftirqd/1 next_pid=20 next_prio=120
            elif tracingBackend == "ftrace":
                commandAndPid = lineContents[0].split("-")
                self.pid = int(commandAndPid[-1])
                self.cpu = int(lineContents[1][1:-1])
                self.command = "-".join(commandAndPid[0:-1])
                self.timeStamp = float(lineContents[2][:-1]) * (
                    10 ** 9
                )  # Converting to nanoseconds
                self.event = lineContents[3][0:-1]
                self.probe = (
                    self.event
                )  # Same as probes aren't mentioned in ftrace like tracepoint:sched:sched_switch
                self.details = dict()
                if len(lineContents) > 5:
                    for content in lineContents[4].strip().split():
                        attribute, value = content.split("=")
                        self.details[attribute] = value
                # TODO Add misertrace required kprobes here
                ftraceEvents = [
                    "tcp_probe",
                    "tcp_rcv_space_adjust",
                    "sys_enter_sendto",
                    "sys_enter_sendmsg",
                    "sys_enter_writev",
                    "sys_enter_write",
                    "sys_exit_sendto",
                    "sys_exit_sendmsg",
                    "sys_exit_writev",
                    "sys_exit_write",
                    "sys_enter_recvfrom",
                    "sys_enter_recvmsg",
                    "sys_enter_readv",
                    "sys_enter_read",
                    "sys_exit_recvfrom",
                    "sys_exit_recvmsg",
                    "sys_exit_readv",
                    "sys_exit_read",
                ]
                self.isImplementation = self.event in ftraceEvents

                # Bringing self.details to a uniform format
                if self.event == "tcp_probe" or self.event == "tcp_rcv_space_adjust":
                    self.details["saddr"] = TraceRecord.parseHexIP(
                        self.details["saddr"]
                    )
                    self.details["daddr"] = TraceRecord.parseHexIP(
                        self.details["daddr"]
                    )

        except:
            print("Error in parsing: ", lineContents)
            exit()

    def parseHexIP(hexIPString: str):
        hexVals = [int(hexVal, 16) for hexVal in hexIPString[6:-1].split(",")]
        if len(hexVals) == 4:
            ip = ".".join(hexVals)
        elif len(hexVals) == 16:
            ip = ".".join(hexVals[4:8])
        return ip
