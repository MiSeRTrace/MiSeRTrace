![KRTrace LOGO](./assets/KRTraceLogo.png)
# KRTrace
**This is an amazing tool. You have been warned**

## What does KRTrace do?
- KRTrace traces the requests to a microservice application along the Linux Kernel
- The tool works on postprocessing of ftrace reports and storing data structures for application threads in the kernel and the communication between them
- Each request upon arrival into the microservice application from the gateway IP is assigned a unique number, the traceID
- The end result of the KRTrace is to provide the **time spent** by the various threads on each traceID and the **flow of requests** of each traceID between threads

## Data Model of KRTrace
- Diagram + Explanation TODO

## How to use this tool?
### Setting up required initial data for tracing
- Start your microservice (Docker) application
- Record idle-always-running PIDS of the application
- Record IPs of the running containers
- The resulting file should be in the format should be in the format : `PID Container_Name Container_IP Container_Hash` separated by whitespace
- The provided utils can be used to obtain the data in this format
- TODO, using utils for initital data`use utils/get-all-pids`

### Running a workload and recording the kernel traces
- `trace-cmd record -e sched_switch -e sched_process_exit -e sched_process_fork -e sys_enter_sendto -e sys_exit_sendto -e inet_sock_set_state -e tcp_probe -e sys_enter_recvfrom -e sys_exit_recvfrom -e tcp_rcv_space_adjust -e sys_enter_sendmsg -e sys_exit_sendmsg -e sys_enter_write -e sys_exit_write -e sys_enter_read -e sys_exit_read -e sys_enter_recvmsg -e sys_exit_recvmsg -O norecord-cmd -O norecord-tgid -O event-fork -O function-fork $(get-all-pids socialnetwork_default | awk '{print
f "-P "$1" "}') -C global -c`
- Wait for the alert "Press Ctrl C to stop recording"
- Run the application workload in parallel
- Halt the trace record (with Ctrl C)


- Generate the trace report for KRTrace
```shell
trace-cmd report -R -i <path to trace.dat> | grep -vEi "^cpu" | sed -E 's/,\s*/,/g' > report.txt
```

- Pass the report and the initial setup file to the program with the IP of the gateway. This is generally the first IP of the docker network. For example if the IP of a service is 172.24.0.6, the gateway IP is usually 172.24.0.**1**
```shell
cat <path to report> | python3 src/generator.py -i **\<path to pids.txt\>** -g **\<Gateway IP\>** [options]
```
- for help
```shell
python3 src/generator.py --help
```

 #### Options for main.py
- **-V** : Applicable to first pass, prints verbose first pass output
- **-R** : Applicable to second pass, prints output in raw format
- **-C** : Print Coloured output wherever possible (Does not apply in the case of raw 2nd pass output)