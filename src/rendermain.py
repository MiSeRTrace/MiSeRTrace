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
    help="pass the path/to/traceProcessor.pickle",
    required=True,
)
parser.add_argument(
    "-rt",
    "--rendertype",
    type=str,
    help="pass the rendertype : " + ",".join([i for i in renderMap.keys()]),
    required=True,
)
parser.add_argument(
    "-o", "--output", type=str, help="pass the path/to/outputfile.json, default STDOUT"
)

parser.add_argument(
    "-r", "--range", type=str, help="pass the range, use with type=custom"
)
parser.add_argument(
    "-t", "--trace", type=str, help="pass the path/to/trace.txt, use with type=custom"
)

parser.add_argument(
    "-R", action="store_true", help="to print output in raw format, use with type=dag"
)
parser.add_argument(
    "-F",
    action="store_true",
    help="to format raw format (works when used with -R), use with type=dag",
)
parser.add_argument(
    "-C",
    action="store_true",
    help="to print colored output (works when used without -R), use with type=dag",
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
