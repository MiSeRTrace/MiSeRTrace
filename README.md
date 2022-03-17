# MiSeRTrace

## What does MiSeRTrace do?

- MiSeRTrace traces the end-to-end path of requests entering a microservice application at the kernel space without requiring instrumentation or modification of the application. 
- Observability at the comprehensiveness of the kernel space allows breaking down of various steps in activities such as network transfers and tasks, thus enabling root cause based performance analysis and accurate identification of hotspots. 
- MiSeRTrace currently supports bpftrace as a tracing backend. ftrace support will also be integrated into MiSerTrace soon.
- Users can enable any of the tracepoints and features provided by bpftrace that they wish to monitor. MiSeRTrace initially identifies the request spans, i.e. the duration spent by a particular thread on servicing a client request or a subsequent internal request. Later each request span is associated with a unique trace. MiSeRTrace subsequently buckets all the time-stamped user-enabled trace logs into the request spans that triggered them.

## How to use MiSeRTrace?

### Setting up required initial data for tracing -

Start your microservice application (MiSeRTrace currently supports Docker as the containerization engine), and then run `gen-init-data.py`.

By default, the OUTPUTBT FILE contains the probes used by MiSeRTrace in its implementation. If you wish to monitor some extra events provided by bpftrace, the .bt file containing these probes has to be passed as the INPUTBT argument.

```
usage: gen-init-data.py [-h] -n NETWORK [-i INPUTBT] -m METAFILE -o OUTPUTBT

arguments:
  -h, --help                        show this help message and exit
  -n NETWORK, --network NETWORK     docker_network_name
  -i INPUTBT, --inputbt INPUTBT     path/to/customInputBtFile.bt, ensure that the filter /@pids[tid] == 1/ is present for every probe so as to trace only the processes in your docker network
  -m METAFILE, --metafile METAFILE  path/to/outputMetaFile.txt
  -o OUTPUTBT, --outputbt OUTPUTBT  path/to/outputBtFile.bt
```

### Running a workload and recording the kernel traces -

```
BPFTRACE_PERF_RB_PAGES=<Buffer size in pages> BPFTRACE_MAP_KEYS_MAX=<Value greater than maximum number of unique pids in the docker network> BPFTRACE_LOG_SIZE=<Size in bytes of the log to store the .bt file> bpftrace <path/to/outputBtFile.bt> > trace.psv
```

Wait for about 60 seconds after bpftrace has been started and before starting the workload so as to ensure that bpftrace has attached all the probes being monitored.

Once the workload is complete, ensure that all the data has been moved from the ring buffers to disk before stopping bpftrace (one possible way is to ensure that size of trace.psv is no longer growing at a large rate).

Pass the captured pipe-separated trace file to `sort-bpftrace-output.py` to ensure the trace logs are globally time-ordered across all CPUs.

```
usage: sort-bpftrace-output.py [-h] -i INPUT -o OUTPUT

arguments:
  -h, --help                  show this help message and exit
  -i INPUT, --input INPUT     path/to/inputTrace.psv
  -o OUTPUT, --output OUTPUT  path/to/sortedOutput.psv

```

### Generating the request traces -

1) To capture the request spans from the trace logs

```
generator.py [-h] -i INPUT -m METAFILE -g GATEWAY -o OUTPUT

arguments:
  -h, --help                        show this help message and exit
  -i INPUT, --input INPUT           path/to/inputTrace.psv, ensure the trace logs are sorted by time
  -m METAFILE, --metafile METAFILE  path/to/metaFile.txt
  -g GATEWAY, --gateway GATEWAY     pass the docker gateway ip in ipv4 format
  -o OUTPUT, --output OUTPUT        path/to/dump.pickle
```

2) To generate request traces from the captured spans

```
usage: rendermain.py [-h] -i INPUT -t RENDERTYPE [-o OUTPUT] [-n RANGE] [-l TRACELOGS] [-r] [-f] [-c]

optional arguments:
  -h, --help                              show this help message and exit
  -i INPUT, --input INPUT                 path/to/dump.pickle
  -t RENDERTYPE, --rendertype RENDERTYPE  dag OR custom
  -o OUTPUT, --output OUTPUT              path/to/outputfile, default STDOUT
  -n RANGE, --range RANGE                 range of request traces to processes, required with type=custom. eg 1-4,6
  -l TRACELOGS, --tracelogs TRACELOGS     path/to/sortedTraceLogs.psv, required with type=custom
  -r                                      to obtain output in raw json format (works when used with -t dag)
  -f                                      to format the raw json (works when used with -r and -t dag)
  -c                                      to print colored output (works when used with -t dag and WITHOUT -r)
```

If the render type chosen is custom, MiSeRTrace enables the ability to provide custom code stubs to process the captured data through-

- The functions `customInit, customConsumeRecord, customRetrieveData and customRecordValid` defined in the class `CustomThreadStateRender` to process the data that belongs to every span.

- The functions `customInit, customConsumeRecord and customRetrieveData` defined in the class `CustomTraceHandler` to process the data associated with every request trace.

## Publication

To obtain more information about the architecture of MiSeRTrace, please look through the following paper. Please cite our work if you found MiSeRTrace helpful.

Thrivikraman V, Vishnu R Dixit, Nikhil Ram S, Vikas K Gowda, Santhosh Kumar Vasudevan, and Subramaniam Kalambur. 2022. MiSeRTrace: Kernel-level Request Tracing for Microservice Visibility. In Companion of the 2022 ACM/SPEC International Conference on Performance Engineering (ICPE ’22), April 9–13, 2022, Bejing, China. ACM, New York, NY, USA, 4 pages. https://doi.org/10.1145/XXXXXX.XXXXXX

<!-- - Record idle-always-running PIDS of the application
- Record IPs of the running containers
- The resulting file should be in the format should be in the format : `PID Container_Name Container_IP Container_Hash` separated by whitespace

- `trace-cmd record -e sched_switch -e sched_process_exit -e sched_process_fork -e sys_enter_sendto -e sys_exit_sendto -e inet_sock_set_state -e tcp_probe -e sys_enter_recvfrom -e sys_exit_recvfrom -e tcp_rcv_space_adjust -e sys_enter_sendmsg -e sys_exit_sendmsg -e sys_enter_write -e sys_exit_write -e sys_enter_read -e sys_exit_read -e sys_enter_recvmsg -e sys_exit_recvmsg -O norecord-cmd -O norecord-tgid -O event-fork -O function-fork $(get-all-pids socialnetwork_default | awk '{print
f "-P "$1" "}') -C global -c`
- Wait for the alert "Press Ctrl C to stop recording"
- Run the application workload in parallel
- Halt the trace record (with Ctrl C)

```shell
trace-cmd report -R -i <path to trace.dat> | grep -vEi "^cpu" | sed -E 's/,\s*/,/g' > report.txt
``` -->
