#!/usr/bin/python3
import psutil
import docker
import argparse
import csv

btScript = """
#include <net/sock.h>
#include <linux/socket.h>
#include <linux/tcp.h>
#include <linux/types.h>
#include <linux/in6.h>
#include <linux/net.h>
#include <linux/pid.h>
#include <linux/pid_namespace.h>
#include <linux/bpf.h>

BEGIN
{
	INIT_PID_MAP
}

tracepoint:tcp:tcp_probe
/@pids[tid] == 1/
{
	$saddr = (args->saddr);
	$daddr = (args->daddr);
	printf("\\"%s\\"|\\"%d\\"|\\"%llu\\"|\\"%d\\"|\\"MT:%s\\"|", comm, tid, nsecs, cpu, probe);
	printf("\\"sport=%d dport=%d saddr=%d.%d.%d.%d ",  args->sport, args->dport, $saddr[4], $saddr[5], $saddr[6], $saddr[7]);
	printf("daddr=%d.%d.%d.%d\\"\\n", $daddr[4], $daddr[5], $daddr[6], $daddr[7]);
}

tracepoint:tcp:tcp_rcv_space_adjust
/@pids[tid] == 1/
{
	$saddr = ntop(args->saddr);
	$daddr = ntop(args->daddr);
	printf("\\"%s\\"|\\"%d\\"|\\"%llu\\"|\\"%d\\"|\\"MT:%s\\"|", comm, tid, nsecs, cpu, probe);	
	printf("\\"sport=%d dport=%d saddr=%s daddr=%s\\"\\n", args->sport, args->dport, $saddr, $daddr);
}

tracepoint:syscalls:sys_enter_sendto,
tracepoint:syscalls:sys_enter_sendmsg,
tracepoint:syscalls:sys_enter_writev,
tracepoint:syscalls:sys_enter_write,
tracepoint:syscalls:sys_exit_sendto,
tracepoint:syscalls:sys_exit_sendmsg,
tracepoint:syscalls:sys_exit_writev,
tracepoint:syscalls:sys_exit_write,
tracepoint:syscalls:sys_enter_recvfrom,
tracepoint:syscalls:sys_enter_recvmsg,
tracepoint:syscalls:sys_enter_readv,
tracepoint:syscalls:sys_enter_read,
tracepoint:syscalls:sys_exit_recvfrom,
tracepoint:syscalls:sys_exit_recvmsg,
tracepoint:syscalls:sys_exit_readv,
tracepoint:syscalls:sys_exit_read
/@pids[tid] == 1/
{
    printf("\\"%s\\"|\\"%d\\"|\\"%llu\\"|\\"%d\\"|\\"MT:%s\\"\\n", comm, tid, nsecs, cpu, probe);
}

tracepoint:sched:sched_process_exit
/@pids[tid] == 1/
{
    printf("\\"%s\\"|\\"%d\\"|\\"%llu\\"|\\"%d\\"|\\"MT:%s\\"|\\"pid=%d\\"\\n", comm, tid, nsecs, cpu, probe, args->pid);
    @pids[args->pid]=0;
}

tracepoint:sched:sched_process_fork
/@pids[tid] == 1/
{
    @pids[args->child_pid] = 1;
    printf("\\"%s\\"|\\"%d\\"|\\"%llu\\"|\\"%d\\"|\\"MT:%s\\"|", comm, tid, nsecs, cpu, probe);
	printf("\\"parent_pid=%d child_pid=%d\\"\\n",args->parent_pid, args->child_pid);
}

kprobe:sock_sendmsg,
kprobe:____sys_sendmsg
/@pids[tid] == 1/
{
	$socket = (struct socket *)arg0;
	$sk = $socket->sk;
	$af = $sk->__sk_common.skc_family;
	if ($af == AF_INET || $af == AF_INET6)
	{
		if ($af == AF_INET)
		{
			$daddr = ntop($af, $sk->__sk_common.skc_daddr);
			$saddr = ntop($af, $sk->__sk_common.skc_rcv_saddr);
		}
		else
		{
			$daddr = ntop($sk->__sk_common.skc_v6_daddr.in6_u.u6_addr8);
			$saddr = ntop($sk->__sk_common.skc_v6_rcv_saddr.in6_u.u6_addr8);	
		}
		$lport = $sk->__sk_common.skc_num;
		$dport = $sk->__sk_common.skc_dport;
		$rPid = (*((struct upid*)($sk->sk_peer_pid->numbers))).ns->pid_allocated ; 
		$dport = ($dport >> 8) | (($dport << 8) & 0x00FF00);
		printf("\\"%s\\"|\\"%d\\"|\\"%llu\\"|\\"%d\\"|\\"MT:tcp_send\\"|", comm, tid, nsecs, cpu);	
	    printf("\\"sport=%d dport=%d saddr=%s daddr=%s\\"\\n", $lport, $dport, $saddr, $daddr);
	}
}

"""

parser = argparse.ArgumentParser()

parser.add_argument(
    "-n", "--network", type=str, help="docker_network_name", required=True
)
parser.add_argument("-i", "--inputbt", type=str, help="path/to/customInputBtFile.bt")
parser.add_argument(
    "-m",
    "--metafile",
    type=str,
    help="path/to/outputMetaFile.psv",
    required=True,
)
parser.add_argument(
    "-o", "--outputbt", type=str, help="path/to/outputBtFile.bt", required=True
)

args = parser.parse_args()

dockerClient = docker.from_env()
APIClient = docker.APIClient(base_url="unix://var/run/docker.sock")

psTreeStore = []


def buildPsList(container, store: list, network: str):
    PID = APIClient.inspect_container(container.id)["State"]["Pid"]
    currentProcess = psutil.Process(PID)
    allProcesses = set(currentProcess.children(recursive=True) + [currentProcess])
    allThreads = set()
    for processPID in allProcesses:
        allThreads |= set(int(i.id) for i in processPID.threads())
        jsonElement = {
            "ID": container.id,
            "Name": container.name,
            "IP": container.attrs["NetworkSettings"]["Networks"][network]["IPAddress"],
            "PID": PID,
            "PIDList": allThreads,
        }
    store.append(jsonElement)


for container in dockerClient.networks.get(args.network).containers:
    buildPsList(container, psTreeStore, args.network)

metaFile = open(args.metafile, "w")
metaCsvWrite = csv.writer(metaFile, delimiter="|")
bpfTraceFile = open(args.outputbt, "w")

initPidStr = ""
for elem in psTreeStore:
    for pid in elem["PIDList"]:
        row = [pid, elem["Name"], elem["IP"], elem["ID"]]
        metaCsvWrite.writerow(row)
        initPidStr += "@pids[" + str(pid) + "]=1;\n\t"

btScript = btScript.replace("INIT_PID_MAP", initPidStr)
print(btScript, file=bpfTraceFile)

if args.inputbt:
    with open(args.inputbt, "r") as inputFile:
        for line in inputFile:
            print(line, file=bpfTraceFile, end="")

metaFile.close()
bpfTraceFile.close()

print(
    'Use Command : "BPFTRACE_PERF_RB_PAGES=<Buffer Size in Pages> BPFTRACE_MAP_KEYS_MAX=<Value greater than maximum number of unique pids in the docker network> BPFTRACE_LOG_SIZE=<Size in bytes of the log to store the .bt file> bpftrace '
    + args.outputbt
    + '> trace.psv"'
)
# print(
#     'eg: "BPFTRACE_PERF_RB_PAGES=131072 BPFTRACE_MAP_KEYS_MAX=4194304 BPFTRACE_LOG_SIZE=750000000 bpftrace '
#     + args.outputbt
#     + '"'
# )
