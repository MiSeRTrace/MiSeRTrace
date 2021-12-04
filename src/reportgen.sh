#!/bin/bash
trace-cmd report -R -i $1 |  grep -vEi "^cpu" | sed -E 's/,\s*/,/g'