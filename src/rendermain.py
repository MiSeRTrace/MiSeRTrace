#!/usr/bin/python3
import argparse
import sys

from render.renderdag import RenderDag
from render.rendercustom import RenderCustom

renderMap = {"dag": RenderDag, "custom": RenderCustom}

parser = argparse.ArgumentParser()
parser.add_argument(
    "-i",
    "--input",
    type=str,
    help="path/to/dump.pickle",
    required=True,
)
parser.add_argument(
    "-t",
    "--rendertype",
    type=str,
    help=" OR ".join([i for i in renderMap.keys()]),
    required=True,
)
parser.add_argument(
    "-o", "--output", type=str, help="path/to/outputfile, default STDOUT"
)
parser.add_argument(
    "-n",
    "--range",
    type=str,
    help="range of request traces to process, eg 1-4,6. All request traces processed by default",
)
parser.add_argument(
    "-l",
    "--tracelogs",
    type=str,
    help="path/to/sortedTraceLogs.psv, required with rendertype=custom",
)
parser.add_argument(
    "-r",
    action="store_true",
    help="to obtain output in raw json format (works when used with rendertype=dag)",
)
parser.add_argument(
    "-f",
    action="store_true",
    help="to format the raw json (works when used with -r and rendertype=dag)",
)
parser.add_argument(
    "-c",
    action="store_true",
    help="to print colored output (works when used with rendertype=dag and WITHOUT -r)",
)
args = parser.parse_args()

outputFile = sys.stdout


if args.rendertype in renderMap:
    pickleDumpFile = open(args.input, "rb")
    if args.output:
        outputFile = open(args.output, "w")
    renderObject = renderMap[args.rendertype](
        pickleDumpFile, args=args, outputFile=outputFile
    )
    renderObject.render(args=args)
    pickleDumpFile.close()
    if args.output:
        outputFile.close()
else:
    print("ERROR: Render Type Invalid")
    exit()
