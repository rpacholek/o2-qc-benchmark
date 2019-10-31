import subprocess
import pexpect
from getpass import getpass
from .base import Statistics, get_password
import os

class Bpf(Statistics):
    def __init__(self, workdir, config):
        self.workdir = workdir
        self.config = config
        
        self.processes = []
        self.files = []

    def run_proc(self, name):
        path = os.path.join(self.workdir, name + ".o")
        proc = pexpect.spawn(f"sudo bash -c './bpf/{name}.py > {path}'")
 
        # Authenticate sudo
        proc.expect("[sudo].*:")
        proc.sendline(get_password())

        self.processes.append(proc)

    def start(self):
        metrics = self.config["stats"]["bpf"]["monitor"] 
        for metric in metrics:
            self.run_proc(metric)

    def stop(self):
        for proc in self.processes:
            pid = proc.pid
            p = pexpect.spawn(f"sudo bash -c 'kill -2 {pid}'")
            p.expect("[sudo].*:")
            p.sendline(get_password())

    def postprocess(self):
        """
        Is triggered after the process is stoped.
        Expected to collect data and save to a file.
        """

    def is_enabled(self):
        return self.config.get("stats", {}).get("bpf", None) is not None

