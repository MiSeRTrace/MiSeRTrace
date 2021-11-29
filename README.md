# kernel-request-tracing

This is an amazing tool
You have been warned

trace-cmd report -R -i <path to trace.dat> | grep -vEi "^cpu" | sed -E 's/,\s*/,/g' > report.txt

cat <path to report> | python3 first-pass/main.py <path to pids.txt> <Gateway IP>