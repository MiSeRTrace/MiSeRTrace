class TraceRecord:
    def __init__(self, line: str):
        # comm 100 9999999999999 tracepoint:sched:sched_process_fork parent_pid=100 child_pid=101
        lineContents = line.strip().split()
        self.command = lineContents[0]
        self.pid = int(lineContents[1])
        self.timeStamp = int(lineContents[2])
        self.event = lineContents[3].split(":")[-1]
        self.details = dict()
        if len(lineContents) > 4:
            for content in lineContents[4:]:
                try:
                    attribute, value = content.split("=")
                    self.details[attribute] = value
                except:
                    print(line)
                    print("Potential error in trace record parsing")
                    exit()
