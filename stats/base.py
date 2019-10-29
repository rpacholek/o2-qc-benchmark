from abc import ABC, abstractmethod
import json
import os.path

class Statistics(ABC):
    def __init__(self, workdir, config):
        self.workdir = workdir
        self.config = config

    def start(self):
        pass

    def lazystart(self):
        """
        Is triggered {test.pre_post_break} after launch,
        where it is expected for the setup to be ready.
        """

    def stop(self):
        """
        Is triggered {test.pre_post_break} before expected end,
        where it is expected for the shutdown sequence to be cut
        Should be light, as it might affect other stat collectors
        """

    def postprocess(self):
        """
        Is triggered after the process is stoped.
        Expected to collect data and save to a file.
        """

    def is_enabled(self):
        return False
    
    def save(self, filename, data):
        with open(os.path.join(self.workdir, filename), "w") as f:
            json.dump(data, f)


