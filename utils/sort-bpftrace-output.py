import argparse
import threading
from time import sleep
from collections import deque
from tqdm import tqdm
import os
import csv

q = deque()

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", type=str, help="pass path/to/inputTrace.psv")
parser.add_argument("-o", "--output", type=str, help="pass path/to/sortedOutput.psv")

args = parser.parse_args()

bufSize = 256  # can be modified or argparse argument can be added

readFp = open(args.input)
# cpuFpList = [open(args.output + "_" + str(i), "w") for i in range(int(args.cpus))]
cpuFpDictWrite = {}
global traceLogsLineCount
traceLogsLineCount = 0
readCsv = csv.reader(readFp, delimiter="|")
for line in readCsv:
    spltList = list(line)
    # print(spltList)
    if len(spltList) >= 4:
        if int(spltList[3]) not in cpuFpDictWrite:
            cpuFpDictWrite[int(spltList[3])] = open(
                args.output + "_" + spltList[3], "w"
            )
        traceLogsLineCount += 1
        print(line, file=cpuFpDictWrite[int(spltList[3])], end="\n")
for i in cpuFpDictWrite:
    cpuFpDictWrite[i].close()


def mergerFunc(writeCsv, cpuCompletedDict, cpuFileBuffer):
    # cpuStore[min(cpuStore, key=lambda i: i[0][0])].pop(0)
    isContinue = True
    tqdmObj = tqdm(desc="SORTING", unit="line", total=traceLogsLineCount)
    while isContinue:
        min = 1000000000000000000000000000000000000
        minkey = -1
        isContinue = False
        for i in cpuCompletedDict:
            if not cpuCompletedDict[i] or cpuFileBuffer[i].__len__():
                isContinue = True
        for i in cpuCompletedDict:
            flag = 0
            while (not cpuCompletedDict[i] or cpuFileBuffer[i].__len__()) and not flag:
                if cpuFileBuffer[i].__len__():
                    flag = 1
                    if min > cpuFileBuffer[i][0][0]:
                        min = cpuFileBuffer[i][0][0]
                        minkey = i
                else:
                    sleep(0.01)
        if minkey != -1:
            writeCsv.writerow(cpuFileBuffer[minkey].popleft()[1])
            tqdmObj.update(1)
            # print(cpuFileBuffer[minkey].popleft()[1], file=write, end="")


cpuFpDictRead = {i: open(args.output + "_" + str(i), "r") for i in cpuFpDictWrite}
# cpuFpList = [open(args.output + "_" + str(i), "r") for i in range(int(args.cpus))]
cpuCompletedDict = {i: False for i in cpuFpDictRead}
cpuFileBuffer = {i: deque(maxlen=bufSize) for i in cpuFpDictRead}
writeFp = open(args.output, "w")


class mergerThread(threading.Thread):
    def __init__(self, writeFp, cpuCompletedDict, cpuFileBuffer):
        threading.Thread.__init__(self)
        self.writeFp = writeFp
        self.cpuCompletedDict = cpuCompletedDict
        self.cpuFileBuffer = cpuFileBuffer
        self.cpuWriter = csv.writer(writeFp, delimiter="|")

    def run(self):
        # print("Starting Merger")
        mergerFunc(self.cpuWriter, self.cpuCompletedDict, self.cpuFileBuffer)


class readerThread(threading.Thread):
    def __init__(self, index, cpuFpDictRead, cpuCompletedDict, cpuFileBuffer):
        threading.Thread.__init__(self)
        self.index = index
        self.cpuCompletedDict = cpuCompletedDict
        self.cpuFileBuffer = cpuFileBuffer
        self.fp = cpuFpDictRead[self.index]
        self.buffer = self.cpuFileBuffer[self.index]

    def run(self):
        # print("Starting Reader", str(self.index))
        for line in self.fp:
            while self.buffer.__len__() == bufSize:
                sleep(0.01)
            lineList = eval(line)
            self.buffer.append([int(lineList[2]), lineList])
        self.cpuCompletedDict[self.index] = True
        # print("Exiting Reader", str(self.index))


readerStore = [
    readerThread(i, cpuFpDictRead, cpuCompletedDict, cpuFileBuffer)
    for i in cpuFpDictRead
]

for thread in readerStore:
    thread.start()
merger = mergerThread(writeFp, cpuCompletedDict, cpuFileBuffer)
merger.start()
for thread in readerStore:
    thread.join()

for cpu in cpuFpDictRead:
    cpuFpDictRead[cpu].close()

merger.join()

writeFp.close()

for i in cpuFpDictWrite:
    os.remove(args.output + "_" + str(i))
