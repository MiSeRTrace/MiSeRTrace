class TraceRecord:
    def __init__(self, line: str):
        # comm 100 9999999999999 tracepoint:sched:sched_process_fork parent_pid=100 child_pid=101
        lineContents = line.strip().split()
        try:
            self.command = lineContents[1]
            self.pid = int(lineContents[2])
            self.timeStamp = int(lineContents[3])
            self.probe = lineContents[4].split(":")
            if self.probe[0] == "ours":
                self.event = self.probe[-1]
                self.details = dict()
                if len(lineContents) > 5:
                    for content in lineContents[5:]:
                        attribute, value = content.split("=")
                        self.details[attribute] = value
            else:
                self.record = line
        except:
            print("Error in parsing: ", line)
            exit()
