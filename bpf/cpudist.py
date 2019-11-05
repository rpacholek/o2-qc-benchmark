#!/usr/bin/env python
# @lint-avoid-python-3-compatibility-imports
#
# cpudist   Summarize on- and off-CPU time per task as a histogram.
#
# USAGE: cpudist [-h] [-O] [-T] [-m] [-P] [-L] [-p PID] [interval] [count]
#
# This measures the time a task spends on or off the CPU, and shows this time
# as a histogram, optionally per-process.
#
# Copyright 2016 Sasha Goldshtein
# Licensed under the Apache License, Version 2.0 (the "License")

from __future__ import print_function
from bcc import BPF
from time import sleep, strftime
from sys import argv

bpf_text = """#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
"""

bpf_text += """
typedef struct pid_key {
    u64 id;
    u64 slot;
} pid_key_t;


BPF_HASH(start, u32, u64);
STORAGE

static inline void store_start(u32 tgid, u32 pid, u64 ts)
{
    if (FILTER)
        return;

    start.update(&pid, &ts);
}

static inline void update_hist(u32 tgid, u32 pid, u64 ts)
{
    if (FILTER)
        return;

    u64 *tsp = start.lookup(&pid);
    if (tsp == 0)
        return;

    if (ts < *tsp) {
        // Probably a clock issue where the recorded on-CPU event had a
        // timestamp later than the recorded off-CPU event, or vice versa.
        return;
    }
    u64 delta = ts - *tsp;
    FACTOR
    STORE
}

struct rq;

int sched_switch(struct pt_regs *ctx, struct rq *rq, struct task_struct *prev)
{
    u64 ts = bpf_ktime_get_ns();
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 tgid = pid_tgid >> 32, pid = pid_tgid;

#ifdef ONCPU
    if (prev->state == TASK_RUNNING) {
#else
    if (1) {
#endif
        u32 prev_pid = prev->pid;
        u32 prev_tgid = prev->tgid;
#ifdef ONCPU
        update_hist(prev_tgid, prev_pid, ts);
#else
        store_start(prev_tgid, prev_pid, ts);
#endif
    }

BAIL:
#ifdef ONCPU
    store_start(tgid, pid, ts);
#else
    update_hist(tgid, pid, ts);
#endif

    return 0;
}
"""

bpf_text = bpf_text.replace('FILTER', '0')
bpf_text = bpf_text.replace('FACTOR', 'delta /= 1000;')
label = "usecs"
section = ""
bpf_text = bpf_text.replace('STORAGE', 'BPF_HISTOGRAM(dist);')
bpf_text = bpf_text.replace('STORE',
        'dist.increment(bpf_log2l(delta));')

b = BPF(text=bpf_text)
b.attach_kprobe(event="finish_task_switch", fn_name="sched_switch")

dist = b.get_table("dist")

f = open(argv[1], "w")

def output():
    def pid_to_comm(pid):
        try:
            comm = open("/proc/%d/comm" % pid, "r").read()
            return "%d %s" % (pid, comm)
        except IOError:
            return str(pid)

    f.write(" ".join([ int(i.value) for i in dist.values()]))
    print([ int(i.value) for i in dist.values()])
    #dist.print_log2_hist(label, section, section_print_fn=pid_to_comm)
    #dist.clear()

from tools import wait_until_kill
wait_until_kill(output)
