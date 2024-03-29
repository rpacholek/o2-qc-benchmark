import time
import os
import itertools
import yaml
import datetime

from launcher import Launcher
from stats import StatisticManager

def time_to_usec(s):
    return int(s[:-1]) * {"s": 1000*1000, "m": 60*1000**2, "h": 60**2*1000**2}[s[-1]]


class BenchmarkContext:
    index = 0

    def __init__(self, params, workdir, config_template, env={}, config={}):
        BenchmarkContext.index+=1

        self.params = params
        self.env = env
        self.config = config
        self.config_template = config_template
        self.workdir = os.path.join(workdir, f"test_{BenchmarkContext.index}")

        self.duration = 0
        self.program_config = os.path.join(os.getcwd(), self.workdir, "benchmark.json")

        self.__create_dir()
        self.__dump_env()
        
        self.__prepare_launcher()
        self.__prepare_stats()

    def __create_dir(self):
        os.mkdir(self.workdir)
        #Create plot dir
        os.mkdir(os.path.join(self.workdir, "plots"))

    def __dump_params(self, params):
        with open(os.path.join(self.workdir, "params.yaml"), "w") as f:
            yaml.dump(params, f)

    def __dump_env(self):
        with open(os.path.join(self.workdir, "env.yaml"), "w") as f:
            yaml.dump(self.env, f)

    def __create_config(self, params):
        data = ""
        with open(self.config_template) as f:
            data = f.read()
            for key, value in params.items():
                data = data.replace(f"${key}", str(value))
        with open(self.program_config, "w") as f:
            f.write(data)

    def __prepare_launcher(self):
        params = self.__prepare_params(self.params)
        executable = self.config["test"]["command"].split() + [ 
                "-b", 
                "--monitoring-backend", self.config["test"]["config"]["monitoring"],
                "--config-path", self.program_config
        ]
        
        self.__dump_params(dict(executable=" ".join(executable), **params))
        self.__create_config(params)

        self.launcher = Launcher(executable, self.workdir, self.env, self.config)

    def __prepare_stats(self):
        self.stats = StatisticManager(self.workdir, self.config)

    def run(self):
        print(f"Running with parameters: {self.params}")

        self.stats.pre()

        self.launcher.run()
        time.sleep(10)
        self.stats.start()
        if self.duration:
           t = datetime.datetime.now() + datetime.timedelta(seconds=self.duration - 10)
           print(f"Launched. Test expected to end at {t.strftime('%H:%M:%S')}")

        try:
            self.launcher.wait()
        except KeyboardInterrupt:
            self.launcher.force_quit()
        self.stats.stop()

        self.stats.post()

    def __prepare_params(self, params):
        params.update(self.config["test"]["config"])

        params["duration"] = time_to_usec(self.config["test"]["duration"])//10**6
        params["delay"] = time_to_usec(self.config["test"]["delay"])//10**6

        self.duration = params["duration"] + params["delay"]

        return params


class Benchmark:

    def __init__(self, config, workdir, config_template):
        timestamp = time.strftime("%m-%dT%H%M%SZ")
        self.workdir = os.path.join(workdir, f"test_{timestamp}")
        self.config = config
        self.config_template = config_template

        self.__create_dir()
        self.__dump_config()

        #Load env
        self.env = dict(os.environ)

    def __create_dir(self):
        os.mkdir(self.workdir)
        #Create plot dir
        os.mkdir(os.path.join(self.workdir, "plots"))

    def __dump_config(self):
        with open(os.path.join(self.workdir, "config.yaml"), "w") as f:
            yaml.dump(self.config, f)

    def __load_parameters(self):
        d = self.config["test"]["parameters"]
        return d.keys(), list(itertools.product(*d.values()))

    def run(self):
        keys, values = self.__load_parameters()
        i = 1
        for value in values:
            print(f"Running test {i} out of {len(values)}")
            i+=1
            params = dict(zip(keys, value))
            benchmark_context = BenchmarkContext(params, self.workdir, self.config_template, self.env, self.config)
            benchmark_context.run()

