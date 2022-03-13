import sys
import argparse
import csv
from tqdm import tqdm
from core.tracerecord import TraceRecord
from core.traceprocessor import *

sys.setrecursionlimit(10000)

# argument parser
parser = argparse.ArgumentParser()
parser.add_argument(
    "-i",
    "--input",
    type=str,
    help="pass the path/to/inputTrace.psv, ensure sorted by time",
    required=True,
)
parser.add_argument(
    "-m", "--meta", type=str, help="pass the path/to/meta.txt", required=True
)
parser.add_argument(
    "-g",
    "--gateway",
    type=str,
    help="pass the gateway ip.in.ipv4.format",
    required=True,
)
parser.add_argument(
    "-d", "--dump", type=str, help="pass the dump/path/dump.pickle", required=True
)

args = parser.parse_args()

traceProcessor = TraceProcessor(inputFilePath=args.meta, gatewayIP=args.gateway)
with open(args.input, "r") as readFile:
    readCsv = csv.reader(readFile, delimiter="|")
    for line in tqdm(readCsv, desc="PROCESSING", unit="line"):
        record = TraceRecord(list(line))
        if not traceProcessor.consumeRecord(record):
            print("Record Validation Failed")
            exit()

traceProcessor.terminate()
print("DUMPING DATA")
traceProcessor.dumpFirstPass(args.dump)
print("Estimated number of requests: ", len(traceProcessor.traceGenesis))
