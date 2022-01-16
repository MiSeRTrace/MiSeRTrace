from os import close
import sys
import argparse

# import sys.core.threadstate as threadState
from render.rendercustom import RenderCustom

parser = argparse.ArgumentParser()
parser.add_argument(
    "-i", "--input", type=str, help="pass the path/to/traceProcessor.pickle"
)
parser.add_argument("-r", "--range", type=str, help="pass the range")
parser.add_argument("-t", "--trace", type=str, help="pass the path/to/trace.txt")

parser.add_argument("-R", action="store_true", help="to print output in raw format")
parser.add_argument(
    "-C", action="store_true", help="to print colored output (works withour -R)"
)
args = parser.parse_args()

pickleDumpFile = open(args.input, "rb")
renderObject = RenderCustom(pickleDumpFile, args=args)
pickleDumpFile.close()
renderObject.render(args=args)
