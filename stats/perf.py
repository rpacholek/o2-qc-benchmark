import subprocess
import pexpect
from getpass import getpass
from .base import Statistics, get_password
import os
import random

class Perf(Statistics):
    def __init__(self, workdir, config):
        self.workdir = workdir
        self.config = config
        
        self.processes = []
        self.files = []

    def __get_pid(self, name):
        try:
            return [ line for line in output.decode().split("\r\n") if name in line ][0].split()[1]
        except Exception:
            pass
        return 0

    def lazystart(self):
        pname = ranodm.choose(self.config["stats"]["perf"]["monitor"])
        fname = os.path.join(self.workdir, f"{pname}-perf.data")
        pid = self.__get_pid(pname)
        if pid:
            command = f"sudo perf record -o {fname} -F 99 -p {pid}"
            self.process = pexpect.spawn(command)
            self.process.expect("[sudo].*")
            self.process.sendline(get_password())

    def stop(self):
        self.process.close()

    def postprocess(self):
        pass 

    def is_enabled(self):
        return self.config.get("stats", {}).get("perf", None) is not None

