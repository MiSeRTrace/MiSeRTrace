from os import name
import sys
import argparse
import subprocess
from core.tracerecord import TraceRecord
from core.traceprocessor import *

sys.setrecursionlimit(10000)

# argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--tracedat", type=str, help="pass the path/to/trace.dat")
parser.add_argument("-i", "--init", type=str, help="pass the path/to/init.txt")
parser.add_argument(
    "-g", "--gateway", type=str, help="pass the gateway ip.in.ipv4.format"
)
parser.add_argument("-d", "--dump", type=str, help="pass the dump/path/directory")
parser.add_argument(
    "-L", action="store_true", help="to print line numbers as records are consumed"
)
parser.add_argument("-V", action="store_true", help="to print verbose output")
parser.add_argument("-C", action="store_true", help="to print colored output")
parser.add_argument("-R", action="store_true", help="to print output in raw format")
args = parser.parse_args()

traceProcessor = TraceProcessor(inputFilePath=args.init, gatewayIP=args.gateway)

printLines = args.L
lineNumber = 1


verbose = args.V
if verbose:
    traceProcessor.toPrint = True
else:
    traceProcessor.toPrint = False

rawFormat = args.R
if rawFormat:
    traceProcessor.rawFormat = True
else:
    traceProcessor.rawFormat = False

colored = args.C
if colored:
    traceProcessor.colored = True
else:
    traceProcessor.colored = False

traceReportProcess = subprocess.Popen(
    "./reportgen.sh " + args.tracedat,
    stdout=subprocess.PIPE,
    shell=True,
    executable="/bin/bash",
)
for lineBytes in iter(lambda: traceReportProcess.stdout.readline(), b""):
    line = lineBytes.decode("utf-8")
    if printLines:
        print(lineNumber, end="")
        lineNumber += 1
    # print("l" + line)
    record = TraceRecord(line)
    if not traceProcessor.consumeRecord(record):
        print("Record Validation Failed")
        exit()

    if printLines:
        print("\n--------\n")

traceProcessor.terminate()
print("Estimated number of requests: ", len(traceProcessor.traceGenesis))
if args.dump:
    traceProcessor.dumpFirstPass(args.dump)
