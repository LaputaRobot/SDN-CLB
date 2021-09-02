import math
import os
import queue
import random
import threading
import time
from pprint import pprint

from networkx import DiGraph
from Node import Switch


class my_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.flow_queue = []

    def run(self) -> None:
        while True:
            num = random.randint(1, 10)
            self.flow_queue.append(num)
            print(self.flow_queue)
            sleep_time = random.randint(1, 3)
            print('sleep ', sleep_time)
            time.sleep(sleep_time)


sw_num = 40
flow_thread_num = 10
path_len = 6.384
flow_num = sw_num * flow_thread_num / 2
flow_table_num=flow_num*path_len


switch_big=flow_table_num/5/sw_num
switch_small=switch_big*4
switch_sum=flow_table_num/sw_num

controller_big= switch_big*(sw_num/4)
controller_small=controller_big*4
print(controller_big)

class C:
    def __init__(self,name):
        self.name=name

    def __str__(self):
        return self.name
c1=C('c1')
c2=C('c2')
temp=c1
c1=c2
print(temp)
print(c1)
