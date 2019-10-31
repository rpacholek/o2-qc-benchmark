import subprocess
import pexpect
from getpass import getpass
from .base import Statistics, get_password
import os
import random
import psutil

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
            command = f"sudo bash -c 'perf record -o {self.fname} -F 99 -p {pid} -a -g && chown alice {self.fname}'"
            self.process = pexpect.spawn(command)
            self.process.expect("[sudo].*:")
            self.process.sendline(get_password())

    def stop(self):
        pass
        #if self.process:
        #    self.process.close()

    def postprocess(self):
        try:
            #p = pexpect.spawn(f"sudo chown alice {self.fname}")
            #if p.isalive() and p.expect(".*"):
            #    p.sendline(get_password())
    
            with open(f"{self.fname}.sc", "w") as f:
                p = pexpect.spawn(f"perf script -i {self.fname}")
                f.write(p.read())
            with open(f"{self.fname}.fold", "w") as f:
                p = pexpect.spawn(f"stackcollapse-perf.pl {self.fname}.sc")
                f.write(p.read())
            with open(f"{self.fname}.svg", "w") as f:
                p = pexpect.spawn(f"flamegraph.pl {self.fname}.fold")
                f.write(p.read())
        except Exception as e:
            print(e)
    
    def is_enabled(self):
        return self.config.get("stats", {}).get("perf", None) is not None

