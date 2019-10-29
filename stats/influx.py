from .base import Statistics
from influxdb import InfluxDBClient
import csv
import time

InfluxStats = [
        ("cpuUsagePercentage", "mean"),
        ("dpl/processing_rate_mb_s", "mean"),
        ("dpl/dropped_incoming_messages", "sum"),
        ("dpl/relayd_messages", "sum"),
        ("dpl/input_rate_mb_s", "mean"),
        ("QC/generator/objects_published", "last"),
        ("QC/task/cycle/blocks_received", "mean"),
        ("QC/task/cycle/objects_published", "mean"),
        ("QC/task/total/blocks_received", "last"),
        ("QC/task/total/objects_published", "last"),
        ("QC/task/total/Rate_objects_published_per_second", "mean"),
        ("QC/task/Publish_duration", "mean"),
        #("QC/task/",)
        ("QC/check/total/objects_received", "last"),
        ("QC/collector/total/objects_received", "last"),
    ]

class Influx(Statistics):
    def __init__(self, workdir, config):
        super().__init__(workdir, config)

    def is_enabled(self):
        return self.config.get("stats", {}).get("influx", None) is not None

    def lazystart(self):
        self.start = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def stop(self):
        self.stop = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def postprocess(self):
        cfg = self.config["stats"]["influx"]["connection"]
        client = InfluxDBClient(cfg["host"], cfg["port"], cfg["user"], cfg["password"], cfg["dbname"])

        start, stop, groupdur = self.start, self.stop, self.config["stats"]["influx"]["parameters"]["grouptime"]
        datafile = {"influx": {}}
        for name, op in InfluxStats:
            query = f'select {op}(value) from test.autogen."{name}" \
                      where time >= \'{start}\' and time < \'{stop}\' \
                      group by time({groupdur}) fill(null)'

            result = client.query(query).get_points()
            data = {"name": name, "operation": op, "group_duration": groupdur}

            r = list(zip(*[[item["time"], item[(set(item.keys()) - {'time'}).pop()]] for item in result]))
            if r:
                data["value"] = list(r[1])
                data["timestamp"] = [ time.mktime(time.strptime(t, "%Y-%m-%dT%H:%M:%SZ")) if t else None for t in r[0]]
            datafile["influx"][name] = data

        self.save("influx.json", datafile)
        
