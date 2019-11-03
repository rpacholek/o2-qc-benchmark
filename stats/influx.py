from .base import Statistics
from influxdb import InfluxDBClient
import csv
import time

InfluxStats = [
	# DPL
        ("cpuUsagePercentage", "mean"),
        ("processing_rate_mb_s", "mean"),
        ("dropped_incoming_messages", "sum"),
        ("dropped_computations", "sum"),
	("malformed_inputs", "sum"),
        ("relayd_messages", "sum"),
        ("input_rate_mb_s", "mean"),
	("inputs/relayed/incomplete", "mean"),
	("inputs/relayed/pending", "mean"),
	("max_input_latency_ms", "max"),
	("min_input_latency_ms", "min"),
	("inputs/relayed/total", "mean"),
	# GENERATOR
        ("QC/generator/total/objects_published", "last"),
        ("QC/generator/rate/objects_published_per_10_sec", "mean"),
	("QC/generator/last/frequency", "mean"),
	# TASK
        ("QC/task/cycle/blocks_received", "mean"),
        ("QC/task/cycle/objects_published", "mean"),
        ("QC/task/total/blocks_received", "last"),
        ("QC/task/total/objects_published", "last"),
        ("QC/task/Publish_duration", "mean"),
        ("QC/task/rate/objects_published_per_second", "mean"),
        ("QC/task/total/activity_duration", "last"),
        ("QC/task/total/rate/objects_published_per_second", "mean"),
        # CHECK
        ("QC/check/Rate_objects_treated_per_second_whole_run", "mean"),
        ("QC/check/Time_between_first_and_last_objects_received", "mean"),
        ("QC/check/Total_number_histos_treated", "mean"),
        ("QC/check/rate/check_duration", "mean"),
        ("QC/check/rate/run_duration", "mean"),
        ("QC/check/rate/store_duration", "mean"),
        ("QC/check/total/objects_published", "last"),
        ("QC/check/total/objects_received", "last"),
        ("QC/check/total/run_duration", "mean"),
        # COLLECTOR
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
        datafile = {}
        for name, op in InfluxStats:
            query = f'select * from test.autogen."{name}" \
                      where time >= \'{start}\' and time < \'{stop}\'' 

            q = client.query(query)
            container = {}
            for entry in q.get_points():
                device = entry.get("dataprocessor_id", "undefined")
                cur_dict = container.get(device, {"timestamp": [], "value": []})
                
                cur_dict["timestamp"].append(entry["time"])
                cur_dict["value"].append(entry["value"])

                container[device] = cur_dict
            for k, v in container.items():
                if k not in datafile:
                    datafile[k] = {}
                #datafile[k][name] = {"name": name, "operation": op, "group_duration": groupdur, **v}
                datafile[k][name] = v
        self.save("influx.json", datafile)
        
