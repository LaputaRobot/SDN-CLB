import logging
import os
import threading
from networkx import DiGraph
import networkx as nx
from Node import Switch, Host, Controller, SwitchNumber, ControllerPower, SwitchCap
import time


def deal_log_file():
    newest_folder = sorted(os.listdir('Result'))[-1]
    local = 1
    with open('Result\\' + newest_folder + '\\' + 'flowNum.csv', 'w') as f:
        f.write('time,src->dst,small,big,sum\n')
        f.write('{},{},{},{},{}\n'.format(time.time(), local, str(0), str(0), str(0)))

    with open('Result\\20210830\\all-con.csv', 'w') as f:
        pass

    for i in range(1, 5):
        with open('Result\\20210830\\Con{}.csv'.format(i), 'w') as f:
            f.write('time,name,load,big,small\n')


class TopMonitor(threading.Thread):
    def __init__(self, topo):
        threading.Thread.__init__(self)
        self.topology = topo

    def run(self) -> None:
        logger = logging.getLogger('top-logger')
        newest_folder = sorted(os.listdir('Result'))[-1]
        logger.setLevel(level=logging.DEBUG)
        handler = logging.FileHandler('Result' + '\\' + newest_folder + '\\' + 'all-con.csv', encoding='UTF-8')
        logger.addHandler(handler)
        while True:
            loads = [con.load for con in self.topology.controllers]
            avg = sum(loads) / len(loads)
            lbr = 0
            if avg != 0:
                lbr = 1 - sum([abs(x - avg) for x in loads]) / (4 * avg)
            logger.info("{},{},{}".format(time.time(), loads, lbr))
            time.sleep(1)


class Topo(object):
    def __init__(self, node_num=SwitchNumber):
        self.controllers = []
        self.switches = []
        self.hosts = []
        self.G = DiGraph()
        deal_log_file()
        self.gen_topology(node_num)
        self.monitor_thread = TopMonitor(self)
        self.monitor_thread.start()

    def gen_topology(self, switch_num):
        self.switches.append('s0')
        for i in range(1, 5):
            controller = Controller('Con{}'.format(i), power=ControllerPower, G=self.G)
            self.controllers.append(controller)

        for i in range(1, switch_num + 1):
            switch = Switch('s{}'.format(i), SwitchCap)
            dp_con_num = (i - 1) % 4
            switch.set_controller(controller=self.controllers[dp_con_num])
            self.switches.append(switch)
            self.G.add_node(switch.name, sw=switch)

            host = Host('h{}'.format(i), '10.0.0.{}'.format(i))
            host.set_switch(switch)
            self.hosts.append(host)

            self.G.add_node(host.ip, host=host)

            self.G.add_edge(host.ip, switch.name)
            self.G.add_edge(switch.name, host.ip)

        for i in range(1, switch_num + 1):
            for j in range(1, 3):
                next_s = i + j
                if next_s > switch_num:
                    next_s -= switch_num
                self.G.add_edge(self.switches[i].name, self.switches[next_s].name)
                self.G.add_edge(self.switches[next_s].name, self.switches[i].name)

    def get_avg_path_len(self):
        path_len = []
        for i in range(1, SwitchNumber + 1):
            for j in range(1, SwitchNumber + 1):
                if i == j:
                    continue
                else:
                    path_len.append(len(nx.shortest_path(self.G, '10.0.0.{}'.format(i), '10.0.0.{}'.format(j))) - 2)
        print(sum(path_len) / len(path_len))

    def run_host(self):
        for host in self.hosts:
            host.gen_flow()


topo = Topo(SwitchNumber)
# topo.get_avg_path_len()
topo.run_host()
