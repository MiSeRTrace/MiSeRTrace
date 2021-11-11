# kernel-request-tracing

This is an amazing tool
You have been warned

trace-cmd report -R -i <path to trace.dat> | sed -E 's/,\s*/,/g'

<!--TODO Regex for removing first few lines with CPU numbers in the report -->

cat <path to report> | python3 first-pass/main.py <path to pids.txt> <Gateway IP>