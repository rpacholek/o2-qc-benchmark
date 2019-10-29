from .bpf import Bpf
from .influx import Influx
from .sar import Sar

class StatisticManager:
    def __init__(self, workdir, config):
        self.collectors = []
        self.workdir = workdir
        self.config = config
        
        collector_cls = [Influx, Bpf, Sar]
        for ccls in collector_cls:
            self.__add_collector(ccls)

    def __add_collector(self, StatCls):
        stat = StatCls(self.workdir, self.config)
        #print(f"Statistic collector {StatCls.__name__} is {'enabled' if stat.is_enabled() else 'disabled'}")
        if stat.is_enabled():
            self.collectors.append(stat)

    def pre(self):
        for c in self.collectors:
            c.start()

    def start(self):
        for c in self.collectors:
            c.lazystart()

    def stop(self):
        for c in reversed(self.collectors):
            c.stop()

    def post(self):
        for c in reversed(self.collectors):
            c.postprocess()


