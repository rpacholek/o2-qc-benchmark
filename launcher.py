import subprocess
import os.path

class Launcher:
    def __init__(self, executable, workdir=None, env=None, config={}):
        self.executable = executable
        self.env = env
        self.config = config
        self.process = None
        
        self.stdout = os.path.join(workdir, "stdout")
        self.stderr = os.path.join(workdir, "stderr")

    def run(self):
        f_stdout = open(self.stdout, "w")
        f_stderr = open(self.stderr, "w")

        self.process = subprocess.Popen(
                self.executable,
                env=self.env,
                stdout=f_stdout,
                stderr=f_stderr
            )

        f_stdout.close()
        f_stderr.close()

    def wait(self, timeout=None):
        if self.process:
            self.process.wait(timeout)

    def is_alive(self):
        return self.pool() == None

    def force_quit(self):
        subprocess.call(["killall", self.executable[0]])

