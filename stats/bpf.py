import subprocess
import pexpect
from getpass import getpass
from .base import Statistics

sudo_password = None
def log_into_sudo():
    global sudo_password
    sudo_password = getpass("Sudo password: ")

class Bpf(Statistics):
    def __init__(self, workdir, config):
        self.workdir = workdir
        self.config = config
        self.metrics = config["stats"]["bpf"]["monitor"]
        self.processes = []
        self.files = []

    def run_proc(self, name):
        proc = pexpect.spawn("sudo ./bpf/run.py")
 
        # Authenticate sudo
        proc.expect("[sudo].*")
        proc.sendline(password)

        fd = open(os.path.join(self.workdir, name + ".o"), "w")
        proc.logfile = fd

        self.processes.append(proc)
        self.files.append(fd)

    def start(self):
        for metric in self.metrics:
            self.run_proc(metric)

    def stop(self):
        for proc in self.processes:
            proc.close()
        for fd in self.files:
            fd.close()

    def postprocess(self):
        """
        Is triggered after the process is stoped.
        Expected to collect data and save to a file.
        """

    def is_enabled(self):
        return self.config.get("stats", {}).get("bpf", None) is not None

