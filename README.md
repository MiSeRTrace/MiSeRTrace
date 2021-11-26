# kernel-request-tracing

This is an amazing tool
You have been warned

trace-cmd report -R -i <path to trace.dat> | grep -vEi "^cpu" | sed -E 's/,\s*/,/g' > report.txt 

<!--TODO 16 or 32 as prev_state in sched_switch - avoid sched_process_exit -->
<!--TODO Verify whether end times are updated where ever it needs to be -->

cat <path to report> | python3 first-pass/main.py <path to pids.txt> <Gateway IP>