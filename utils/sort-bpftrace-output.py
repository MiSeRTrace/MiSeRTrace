import argparse
import threading
from time import sleep
import os
from collections import deque

q = deque()

parser = argparse.ArgumentParser()

parser.add_argument(
    "-c", "--cpus", type=str, help="pass number of cpus in the traced machine"
)
parser.add_argument("-t", "--trace", type=str, help="pass path/to/trace.txt")
parser.add_argument("-o", "--output", type=str, help="pass path/to/sorted_output.txt")

args = parser.parse_args()

bufSize = 256  # can be modified or argparse argument can be added

readFp = open(args.trace)
cpuFpList = [open(args.output + "_" + str(i), "w") for i in range(int(args.cpus))]
c = 0
for line in readFp:
    spltList = line.split()
    if len(spltList) >= 4:
        c += 1
        print(line, file=cpuFpList[int(spltList[3])], end="")
print("COUNT", c)
for i in range(len(cpuFpList)):
    cpuFpList[i].close()


def mergerFunc(writeFp, cpuCompletedList, cpuFileBuffer):
    # cpuStore[min(cpuStore, key=lambda i: i[0][0])].pop(0)
    isContinue = True
    while isContinue:
        min = 1000000000000000000000000000000000000
        minkey = -1
        isContinue = False
        for i in range(len(cpuCompletedList)):
            if not cpuCompletedList[i] or cpuFileBuffer[i].__len__():
                isContinue = True
        for i in range(len(cpuCompletedList)):
            flag = 0
            while (not cpuCompletedList[i] or cpuFileBuffer[i].__len__()) and not flag:
                if cpuFileBuffer[i].__len__():
                    flag = 1
                    if min > cpuFileBuffer[i][0][0]:
                        min = cpuFileBuffer[i][0][0]
                        minkey = i
                else:
                    sleep(0.01)
        if minkey != -1:
            print(cpuFileBuffer[minkey].popleft()[1], file=writeFp, end="")


cpuFpList = [open(args.output + "_" + str(i), "r") for i in range(int(args.cpus))]
cpuCompletedList = [False for i in range(len(cpuFpList))]
cpuFileBuffer = [deque(maxlen=bufSize) for i in range(len(cpuFpList))]
writeFp = open(args.output, "w")


class mergerThread(threading.Thread):
    def __init__(self, writeFp, cpuCompletedList, cpuFileBuffer):
        threading.Thread.__init__(self)
        self.writeFp = writeFp
        self.cpuCompletedList = cpuCompletedList
        self.cpuFileBuffer = cpuFileBuffer

    def run(self):
        print("Starting Merger")
        mergerFunc(self.writeFp, self.cpuCompletedList, self.cpuFileBuffer)
        print("Exiting Merger")


class readerThread(threading.Thread):
    def __init__(self, index, cpuFpList, cpuCompletedList, cpuFileBuffer):
        threading.Thread.__init__(self)
        self.index = index
        self.cpuFpList = cpuFpList
        self.cpuCompletedList = cpuCompletedList
        self.cpuFileBuffer = cpuFileBuffer
        self.fp = self.cpuFpList[self.index]
        self.buffer = self.cpuFileBuffer[self.index]

    def run(self):
        print("Starting Reader", str(self.index))
        for line in self.fp:
            while self.buffer.__len__() == bufSize:
                sleep(0.01)
            self.buffer.append((int(line.split()[2]), line))
        self.cpuCompletedList[self.index] = True
        print("Exiting Reader", str(self.index))


readerStore = [
    readerThread(i, cpuFpList, cpuCompletedList, cpuFileBuffer)
    for i in range(int(args.cpus))
]

for thread in readerStore:
    thread.start()
merger = mergerThread(writeFp, cpuCompletedList, cpuFileBuffer)
merger.start()
for thread in readerStore:
    thread.join()

for file in cpuFpList:
    file.close()

merger.join()

writeFp.close()

for i in range(int(args.cpus)):
    os.remove(args.output + "_" + str(i))
