import sys

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
	$saddr = ntop((((struct sockaddr_in6 *)(args->saddr))->sin6_addr).in6_u.u6_addr8);
	$daddr = ntop((((struct sockaddr_in6 *)(args->daddr))->sin6_addr).in6_u.u6_addr8);
	printf("%s %d %llu %s ", comm, tid, nsecs, probe);	
	printf("saddr=%s daddr=%s sport=%d dport=%d\\n", $saddr, $daddr, args->sport, args->dport);
}

tracepoint:tcp:tcp_probe
/@pids[tid] == 1/
{
	$saddr = (args->saddr);
	$daddr = (args->daddr);
	printf("%s %d %llu %s", comm, tid, nsecs, probe);	
	printf("saddr=%d.%d.%d.%d ", $saddr[4], $saddr[5], $saddr[6], $saddr[7]);
	printf("daddr=%d.%d.%d.%d ", $daddr[4], $daddr[5], $daddr[6], $daddr[7]);
	printf("sport=%d dport=%d\\n", args->sport, args->dport);
}


tracepoint:tcp:tcp_rcv_space_adjust
/@pids[tid] == 1/
{
	$saddr = ntop(args->saddr);
	$daddr = ntop(args->daddr);
	printf("%s %d %llu %s ", comm, tid, nsecs, probe);	
	printf("saddr=%s daddr=%s sport=%d dport=%d\\n", $saddr, $daddr, args->sport, args->dport);
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
    printf("%s %d %llu %s\\n", comm, tid, nsecs, probe);
}

tracepoint:sched:sched_process_exit
/@pids[tid] == 1/
{
    printf("%s %d %llu %s pid=%d\\n", comm, tid, nsecs, probe, args->pid);
    @pids[args->pid]=0;
}

tracepoint:sched:sched_process_fork
/@pids[tid] == 1/
{
    @pids[args->child_pid] = 1;
    printf("%s %d %llu %s parent_pid=%d child_pid=%d\\n", comm, tid, nsecs, probe, args->parent_pid, args->child_pid);
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
		$lport = $sk->sk_num;
		$dport = $sk->sk_dport;
		$rPid = (*((struct upid*)($sk->sk_peer_pid->numbers))).ns->pid_allocated ; 
		$dport = ($dport >> 8) | (($dport << 8) & 0x00FF00);
		printf("%s %d %llu %s ", comm, tid, nsecs, probe);	
	    printf("saddr=%s daddr=%s sport=%d dport=%d\\n",   $saddr, $daddr, $lport, $dport);
	}
}
"""

init_pid = ""
for i in sys.argv[1:]:
    init_pid += "@pids[" + i + "]=1;\n\t"

btScript = btScript.replace("INIT_PID_MAP", init_pid)
print(btScript)
