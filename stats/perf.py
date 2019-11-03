import subprocess
import pexpect
from getpass import getpass
from .base import Statistics, get_password
import os
import random
import psutil
import traceback

class Perf(Statistics):
    def __init__(self, workdir, config):
        self.workdir = workdir
        self.config = config
        
        self.process = None
        self.fname = None

    def __get_pid(self, name, pattern):
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if proc.info["name"] == name:
                p = " ".join(proc.cmdline())
                if "--id " + pattern in p:
                    return proc.info["pid"]
        return 0
        
    def lazystart(self):
        pname = random.choice(self.config["stats"]["perf"]["monitor"])
        self.fname = os.path.join(self.workdir, f"{pname}-perf.data")
        pid = self.__get_pid(self.config["test"]["command"], pname)
        if pid:
            command = f"sudo bash -c 'perf record -o {self.fname} -F 99 -p {pid} -a -g --call-graph dwarf  && chown alice {self.fname}'"
            self.process = pexpect.spawn(command)
            self.process.expect("[sudo].*:")
            self.process.sendline(get_password())

    def stop(self):
        pass
        #if self.process:
        #    self.process.close()

    def postprocess(self):
        try:
            pexpect.spawn(f"bash -c 'perf script -i {self.fname} > {self.fname}.sc'", timeout=30).wait()
            pexpect.spawn(f"bash -c 'stackcollapse-perf.pl {self.fname}.sc > {self.fname}.fold'", timeout=30).wait()
            pexpect.spawn(f"bash -c 'flamegraph.pl {self.fname}.fold > {self.fname}.svg'", timeout=30).wait()
        except Exception as e:
            print(traceback.format_exc())
            print(e)
    
    def is_enabled(self):
        return self.config.get("stats", {}).get("perf", None) is not None

