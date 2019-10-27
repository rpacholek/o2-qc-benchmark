from .base import Statistics
from influxdb import InfluxDBClient
import csv
import time

InfluxStats = [
        ("dpl/processing_rate_mb_s", "mean"),
        ("dpl/dropped_incoming_messages", "sum"),
        ("cpuUsagePercentage", "mean"),
        ("dpl/relayd_messages", "sum"),
        ("dpl/input_rate_mb_s", "mean"),
        ("QC_task_objects_published", "mean"),
        ("QC_checker_received_objects", "mean"),
        ("QC_task_objects_received", "mean"),
        ("producer", "mean"),
        ("monitorData", "mean")
    ]

class Influx(Statistics):
    def __init__(self, test_name, workdir, config):
        super().__init__(test_name, workdir, config)

    def start(self):
        self.start = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def stop(self):
        self.stop = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def postprocess(self):
        connection_config = self.config["stats"]["influx"]["connection"]
        client = InfluxDBClient(**connection_config)

        start, stop, groupdur = self.start, self.stop, self.config["stats"]["influx"]["parameters"]["grouptime"]
        datafile = {"influx": {}}
        for name, op in names:
            query = f'select {op}(value) from test.autogen."{name}" \
                      where time >= \'{start}\' and time < \'{stop}\' \
                      group by time({groupdur}) fill(null)'

            result = client.query(query).get_points()
            data = {"name": name, "operation": op, "group_time": grouptime}

            r = list(zip(*[ item.values() for item in result ]))
            if r:
                data["value"] = list(r[0])
                data["timestamp"] = [ time.mktime(time.strptime(t, "%Y-%m-%dT%H:%M:%SZ")) for t in r[1]]
            datafile["influx"][name] = data

        self.save("influx.json", dafafile)
        
