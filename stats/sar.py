from .base import Statistics
import os.path
import subprocess
import distutils.spawn
import csv

SarParams = {
    "memory": {
        "param": "-r",
        "title": "Memory",
        "plots": [
            {"title": "Memory", "cols": ["kbmemused", "kbbuffers", "kbcached"], "type": None}
            ]
        },
    "cpu": {
        "param": "-u",
        "title": "CPU",
        "plots": [
            {"title": "CPU", "cols": "%user;%nice;%system;%iowait;%steal;%idle".split(";"), "type": None}
        ]
        },
    "paging": {
        "param": "-B",
        "title": "Paging",
        "plots": [
            {"title": "Paging", "cols": "pgpgin/s;pgpgout/s;fault/s;majflt/s;pgfree/s;pgscank/s;pgscand/s;pgsteal/s".split(";"), "type": None}
        ]
        },
    "TCP": {
        "param": "-n TCP",
        "title": "TCP",
        "plots": [
            {"title": "TCP", "cols": "active/s;passive/s;iseg/s;oseg/s".split(";"), "type": None}
        ]
        },
    "UDP": {
        "param": "-n UDP",
        "title": "UDP",
        "plots": [
            {"title": "UDP", "cols": "idgm/s;odgm/s;noport/s;idgmerr/s".split(";"), "type": None}
        ]
        },
    "switch": {
        "param": "-w",
        "title": "task creation and system switching activity",
        "plots": [
            {"title": "Content switch", "cols": "cswch/s".split(";"), "type": None}
        ]
    }
}

class Sar(Statistics):
    def __init__(self, workdir, config):
        super().__init__(workdir, config)
        self.process = None
        self.name = "sar.o"
        self.path = os.path.join(self.workdir, self.name)

    def is_enabled(self):
        return self.config.get("stats", {}).get("sar", None) is not None

    def lazystart(self):
        if distutils.spawn.find_executable("sar"):
            self.f = open("/dev/null", "w")
            self.process = subprocess.Popen("sar -o {} -n TCP -n UDP -P ALL -Bruw 1".format(self.path).split(" "), stdout=self.f)
        else:
            self.process = None

    def stop(self):
        if self.process:
            self.process.send_signal(2)
            self.process.send_signal(15)
            self.f.close()

    def postprocess(self):
        datafile = {}
        for group in self.config["stats"]["sar"]["monitor"]:
            data = self.__sadf(self.path, SarParams[group]["param"])
            data = self.__decode_sar(data)
            timestamps, data = self.__filter_sar(data)

            groupdata = {}
            for key, value in data.items():
                groupdata[key] = { "timestamp": timestamps, "value": value }
            datafile[group] = groupdata
        
        self.save("sar.json", datafile)


    def __sadf(self, filename, param):
        command ="sadf -t -d -C {} -- {}".format(filename, param).split(" ") 
        p = subprocess.run(command, stdout=subprocess.PIPE)
        #stdout, _stderr = p.communicate()
        return p.stdout.decode()

    def __decode_sar(self, data):
        iterator = csv.reader(data.splitlines(), delimiter=';')
        header = next(iterator)
        matrix = zip(*list(iterator))
        matrix = [ [float(s.replace(",",".")) for s in row] if set(row[0]).issubset(set("1234567890,")) else row for row in matrix ]
        return dict(zip(header, matrix))

    def __filter_sar(self, data, columns=None):
        data = data.copy()

        timestamps = data["timestamp"]
        drops = (set(data.keys()) - set(columns or set(data.keys()))) | {"# hostname", "interval", "timestamp"}
        for drop in drops:
            del data[drop]
        return timestamps, data
    
