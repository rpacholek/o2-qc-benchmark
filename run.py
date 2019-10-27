import sys
import yaml

from benchmark import Benchmark

def load_config(path):
    with open(path) as f:
        config = yaml.load(f)
    return config

if __name__ == '__main__':
    config = load_config(sys.argv[1])
    workdir, template = sys.argv[2:]

    Benchmark(config, workdir, template).run()

