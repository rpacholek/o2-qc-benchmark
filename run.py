import sys
import yaml
import time

from benchmark import Benchmark
from stats.bpf import log_into_sudo

def load_config(path):
    with open(path) as f:
        config = yaml.load(f)
    return config

if __name__ == '__main__':
    log_into_sudo()
    config = load_config(sys.argv[1])
    workdir, template = sys.argv[2:]

    Benchmark(config, workdir, template).run()
