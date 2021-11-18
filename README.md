# kernel-request-tracing

This is an amazing tool
You have been warned

trace-cmd report -R -i <path to trace.dat> | sed -E 's/,\s*/,/g'

<!--TODO Regex for removing first few lines with CPU numbers in the report -->
<!--TODO Handling case of multiple recvfrom for one request to nginx - ensure to add only one state -->
<!--TODO 16 or 32 as prev_state in sched_switch - avoid sched_process_exit -->
<!--TODO Verify whether end times are updated where ever it needs to be -->
<!--TODO Moving thread states from intermediate log to the log -->

cat <path to report> | python3 first-pass/main.py <path to pids.txt> <Gateway IP>