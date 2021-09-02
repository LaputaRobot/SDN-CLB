import logging
import os
import threading
import time
from lib import Flow
from networkx import DiGraph
import networkx as nx
import numpy as np

SwitchNumber = 16
SwitchCap = 3
flow_of_each_host = 10
ControllerPower = 200

numSmall = 0
numBig = 0
numSum = 0


class ControllerMonitor(threading.Thread):
    def __init__(self, controller):
        threading.Thread.__init__(self)
        self.controller = controller

    def run(self) -> None:
        while True:
            self.controller.del_dumpy_flow()
            self.controller.get_load()
            self.controller.controller_logger.info(
                "{},{},{},{},{},{}".format(time.time(), self.controller.name,
                                           self.controller.load,
                                           self.controller.big_flow_num,
                                           self.controller.small_flow_num,
                                           self.controller.switches_lowest_flow))
            time.sleep(1)


class SwitchMonitor(threading.Thread):
    def __init__(self, switch):
        threading.Thread.__init__(self)
        self.switch = switch

    def run(self) -> None:
        while True:
            self.switch.del_dumpy_flow_table()
            self.switch.get_lowest_flow()
            # print('{}: big: {}, small: {}'.format(self.switch.name,self.switch.big_flow,self.switch.small_flow))
            time.sleep(1)


class Controller(object):
    def __init__(self, name, power, G: DiGraph):
        self.G = G
        self.name = name
        self.power = power
        self.switches = []
        self.switches_lowest_flow = []
        self.packet_in_flow = {}
        self.load = 0
        self.big_flow_num = 0
        self.small_flow_num = 0
        # self.path_len_win=[]
        self.controller_logger = logging.getLogger('Logger-{}'.format(self.name))
        self.set_logger()
        self.monitor_thread = ControllerMonitor(self)
        self.monitor_thread.start()

    def set_logger(self):
        newest_folder = sorted(os.listdir('Result'))[-1]
        self.controller_logger.setLevel(level=logging.DEBUG)
        handler = logging.FileHandler('Result' + '\\' + newest_folder + '\\' +
                                      '{}.csv'.format(
                                          self.name),
                                      encoding='UTF-8')
        self.controller_logger.addHandler(handler)

    def deal_packet_in(self, switch, flow: Flow, flag):
        if switch not in self.switches:
            self.switches.append(switch)
            self.packet_in_flow[switch] = []
        # print('flow in controller')
        if flow.rate > 9:
            print('big flow {} at {} from {}'.format(flow, self.name, switch.name))
        if flag == 'deal in controller':
            self.packet_in_flow[switch].append(flow)
        if flag == 'deal in controller no out':
            self.packet_in_flow[switch].append(flow)
            return
        next_switch = self.get_next_hop(switch.name, flow.src, flow.dst)
        if not next_switch:
            return
        next_switch.deal_of_flow(flow)

    def del_dumpy_flow(self):
        for switch in self.packet_in_flow:
            rm_list = []
            for flow in self.packet_in_flow[switch]:
                if flow.start_time + flow.len_of_time < time.time():
                    rm_list.append(flow)
            for flow in rm_list:
                self.packet_in_flow[switch].remove(flow)

    def get_next_hop(self, dp_name, src, dst):
        path = self.get_path(src, dst)
        next_hop = self.G.nodes[path[path.index(dp_name) + 1]]
        return next_hop.get('sw')

    def get_path(self, src, dst):
        return nx.shortest_path(self.G, src, dst)

    def get_load(self):
        self.load = 0
        self.big_flow_num = 0
        self.small_flow_num = 0
        self.switches_lowest_flow = []

        for switch in self.packet_in_flow:
            self.switches_lowest_flow.append(switch.lowest_flow.rate)
            rm_list = []
            flag = 0
            for flow in self.packet_in_flow[switch]:
                if switch.lowest_flow.rate < flow.rate and flag == 0:
                    print('replace flow {} by controller {}'.format(flow, self.name))
                    rm_list.append(flow)
                    self.packet_in_flow[switch].append(switch.lowest_flow)
                    switch.flowTable.append(flow)
                    flag = 1
                    switch.get_lowest_flow()
                else:
                    if flow.rate > 9:
                        self.big_flow_num += 1
                    else:
                        self.small_flow_num += 1
                    self.load += flow.rate

            for flow in rm_list:
                self.packet_in_flow[switch].remove(flow)

    def print_load(self):
        print('{}---{}-big-{}-small-{}'.format(self.name, self.load, self.big_flow_num, self.small_flow_num))


class Switch(object):
    def __init__(self, name, cap=5):
        self.name = name
        self.hosts = []
        self.controller = None
        self.flowTable = []
        self.flow_table_capacity = cap
        self.big_flow_num = 0
        self.small_flow_num = 0
        self.lowest_flow = None
        self.monitor_thread = SwitchMonitor(self)
        self.monitor_thread.start()

    def deal_of_flow(self, flow: Flow):
        if flow.rate > 9:
            print('deal flow {} in switch {}'.format(flow, self.name))
        flag = 'deal in controller'
        if len(self.flowTable) < self.flow_table_capacity:
            if flow.rate > 9:
                print(self.name, ' just add flow tale {}, flow table len is '.format(flow), len(self.flowTable))
            self.flowTable.append(flow)
            flag = 'deal in switch'
        elif flow.rate > self.lowest_flow.rate:
            temp=self.lowest_flow
            if flow.rate > 9:
                print('{}, flow table is over, replace flow table: {} -> {}'.format(self.name, self.lowest_flow.rate,
                                                                                    flow.rate))
            self.replace_flow_table(self.lowest_flow, flow)
            self.controller.deal_packet_in(self, temp, flag='deal in controller no out')
            flag = 'deal in switch'
        self.controller.deal_packet_in(self, flow, flag=flag)
        self.get_lowest_flow()

    def replace_flow_table(self, flow1, flow2):
        """
        replace flow1 to flow2 in switch flow table

        :param flow1: flow to be replaced
        :param flow2: new flow in table
        :return: None
        """
        self.flowTable.remove(flow1)
        self.flowTable.append(flow2)
        self.lowest_flow=flow2

    def del_dumpy_flow_table(self):
        rm_list = []
        for flow in self.flowTable:
            if flow.start_time + flow.len_of_time < time.time():
                rm_list.append(flow)
        for flow in rm_list:
            self.flowTable.remove(flow)

    def get_lowest_flow(self):
        print('get lowest_flow in {}'.format(self.name))
        min_flow_rate = 1000
        self.big_flow_num = 0
        self.small_flow_num = 0
        for flow in self.flowTable:
            if flow.rate > 9:
                self.big_flow_num += 1
            else:
                self.small_flow_num += 1
            if flow.rate < min_flow_rate:
                min_flow_rate=flow.rate
                self.lowest_flow = flow

    def set_controller(self, controller: Controller):
        self.controller = controller


class FlowThread(threading.Thread):
    def __init__(self, is_big, name, seedNum, local, node_num, switch: Switch):
        threading.Thread.__init__(self)
        self.node_num = node_num
        self.local = local
        self.local_ip = '10.0.0.{}'.format(self.local)
        self.isBig = is_big
        self.name = name
        self.times = 0
        self.firstSleep = False
        self.switch = switch
        np.random.seed(seedNum)

    def run(self):
        global numBig, numSmall, numSum
        newest_folder = sorted(os.listdir('Result'))[-1]
        while True:
            dst = np.random.randint(1, self.node_num + 1)
            if dst == self.local:
                continue
            dst_ip = '10.0.0.%d' % dst
            port = np.random.randint(100, 60000)
            # port=52918
            arrival_inter = np.random.exponential(100)
            # print('{} arrivalInter: {}'.format(self.name, arrival_inter))
            time.sleep(arrival_inter)

            if self.isBig == 1:
                rate = np.random.randint(10, 20)
                # rate = 10
                serve_inter = np.random.exponential(100)
            else:
                rate = np.random.randint(10, 20) / 10
                # rate = 1
                serve_inter = np.random.exponential(100)
            startT = time.time()
            self.times += 1
            # print('{}-{}, {}, gen flow from {} to {},  rate: {}, port: {}, len {}'.format(self.name, self.times, startT,
            #                                                                               self.local_ip, dst_ip, rate,
            #                                                                               port, serve_inter))
            with open('Result\\' + newest_folder + '\\' + 'flowNum.csv', 'a+') as f:
                # strL = f.readlines()[-1].split(',')
                # if len(strL) == 5:
                #     numSmall = int(strL[-3])
                #     numBig = int(strL[-2])
                #     numSum = int(strL[-1])
                if self.isBig == 1:
                    numBig += 1
                    numSum += 1
                else:
                    numSmall += 1
                    numSum += 1
                f.write('{},{}->{},{},{},{}\n'.format(time.time(), self.local, dst, str(numSmall), str(numBig),
                                                      str(numSum)))
            flow = Flow(time.time(), self.local_ip, dst_ip, port, rate, len_of_time=serve_inter)
            self.switch.deal_of_flow(flow)
            time.sleep(serve_inter)
            with open('Result\\' + newest_folder + '\\' + 'flowNum.csv', 'a+') as f:
                # strL = f.readlines()[-1].split(',')
                # if len(strL) == 5:
                #     numSmall = int(strL[-3])
                #     numBig = int(strL[-2])
                #     numSum = int(strL[-1])
                if self.isBig == 1:
                    numBig -= 1
                    numSum -= 1
                else:
                    numSmall -= 1
                    numSum -= 1
                f.write('{},{},{},{},{}\n'.format(time.time(), self.local, str(numSmall), str(numBig), str(numSum)))
            duration = time.time() - startT
            # print('end, {}, {}, duration: {}'.format(self.name, time.time(), duration))


class Host(object):
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self.switch: Switch = None
        self.flow_thread = None
        self.run_flow_thread_flag = False

    def set_switch(self, sw: Switch):
        self.switch = sw

    def send_flow(self, flow: Flow):
        self.switch.deal_of_flow(flow)

    def gen_flow(self):
        local = int(self.ip.split('.')[-1])
        print('{} scapy ...............'.format(self.name))
        local_seed_num = local * flow_of_each_host
        np.random.seed(local_seed_num)
        big = 0
        small = 0
        big_index = np.random.choice(flow_of_each_host, int(flow_of_each_host / 5))
        for i in range(flow_of_each_host):
            if i in big_index:
                big += 1
                thread_seed = local_seed_num + big
                FlowThread(is_big=1, name='{}-Big-{}'.format(self.name, big), seedNum=thread_seed, local=local,
                           node_num=SwitchNumber, switch=self.switch).start()
            else:
                small += 1
                thread_seed = local_seed_num + small + int(flow_of_each_host / 5)
                FlowThread(is_big=0, name='{}-Small-{}'.format(self.name, small), seedNum=thread_seed, local=local,
                           node_num=SwitchNumber, switch=self.switch).start()
