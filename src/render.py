import pickle
import sys

# import traceprocessor

pickleData = None
with open(sys.argv[1], "rb") as pickleDumpFile:
    pickleData = pickle.load(pickleDumpFile)
print(type(pickleData))
print(len(pickleData.traceGenesis))
