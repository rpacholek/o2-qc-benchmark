#!/usr/bin/python
#
# vfsreadlat.py		VFS read latency distribution.
#			For Linux, uses BCC, eBPF. See .c file.
#
# Written as a basic example of a function latency distribution histogram.
#
# USAGE: vfsreadlat.py [interval [count]]
#
# The default interval is 5 seconds. A Ctrl-C will print the partially
# gathered histogram then exit.
#
# Copyright (c) 2015 Brendan Gregg.
# Licensed under the Apache License, Version 2.0 (the "License")
#
# 15-Aug-2015	Brendan Gregg	Created this.

from __future__ import print_function
from bcc import BPF
from ctypes import c_ushort, c_int, c_ulonglong
from time import sleep
from sys import argv
from tools import wait_until_kill

# arguments
interval = 5
count = -1

bpf_text = """
#include <uapi/linux/ptrace.h>

BPF_HASH(start, u32);
BPF_HISTOGRAM(dist);

int do_entry(struct pt_regs *ctx)
{
	u32 pid;
	u64 ts, *val;

	pid = bpf_get_current_pid_tgid();
	ts = bpf_ktime_get_ns();
	start.update(&pid, &ts);
	return 0;
}

int do_return(struct pt_regs *ctx)
{
	u32 pid;
	u64 *tsp, delta;

	pid = bpf_get_current_pid_tgid();
	tsp = start.lookup(&pid);

	if (tsp != 0) {
		delta = bpf_ktime_get_ns() - *tsp;
		dist.increment(bpf_log2l(delta / 1000));
		start.delete(&pid);
	}

	return 0;
}
"""

# load BPF program
b = BPF(text = bpf_text)
b.attach_kprobe(event="sock_recvmsg", fn_name="do_entry")
b.attach_kretprobe(event="sock_recvmsg", fn_name="do_return")

print("Start listening to Sock Recvmsg")
# output

f = open(argv[1], "w")
def output():
    f.write(" ".join([ str(int(i.value)) for i in b["dist"].values() ]))
    print([ int(i.value) for i in b["dist"].values() ])
    #b["dist"].print_log2_hist("usecs")
    #b["dist"].clear()

wait_until_kill(output)

