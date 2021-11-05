class TraceRecord():
    def __init__(self, line: str):
        # <idle>-0     [016] 56701.429653: sched_switch:          prev_comm=swapper/16 prev_pid=0 prev_prio=120 prev_state=0 next_comm=mongod next_pid=23939 next_prio=120
        lineContents = line.strip().split()
        self.command = "-".join(lineContents[0].split('-')[:-1])
        self.pid = int(lineContents[0].split('-')[-1])  # 0 is command-pid
        self.cpu = int(lineContents[1][1:-1])  # 1 is cpu in the format [cpuNo]
        self.timeStamp = float(lineContents[2][:-1])  # 2 is timestamp with ':'
        self.event = lineContents[3][:-1]  # 3 is the event with ':'
        self.details = dict(
        )  # 4 is the dictionary to store all attributes of the event
        for content in lineContents[4:]:
            # In case there isn't any key value pair
            try:
                attribute, value = content.split('=')
                self.details[attribute] = value
            except:
                print("Potential error in trace record parsing")
                exit()

        if self.event == "tcp_rcv_space_adjust" or self.event == "tcp_probe":
            self.details["saddr"] = self.extractAddr("saddr")
            self.details["daddr"] = self.extractAddr("daddr")

    def extractAddr(self, addrType):
        addr = self.details[addrType][6:-1].split(",")
        if len(addr) == 4:
            return ",".join(addr)
        else:
            return ",".join(addr[4:8])
