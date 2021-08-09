#! /usr/bin/env python3
import json
import pickle
import sys, os
import threading
from pprint import pprint

import networkx as nx
import numpy as np
import math
import time
from scapy.all import *
from scapy.layers.inet import IP, UDP, Ether, TCP
# G=nx.DiGraph()
# GR=pickle.load(open('netGraph','rb'))
# for i in range(1,17):
#     G.add_edge('10.0.0.{}'.format(i),i)
#     G.add_edge(i,'10.0.0.{}'.format(i),attr_dict=GR[i]['10.0.0.{}'.format(i)]['attr_dict'])
#     for j in range(1,3):
#         next=i+j
#         if next>16:
#             next-=16
#         G.add_edge(i,next,attr_dict=GR[i][next]['attr_dict'])
#         G.add_edge(next,i,attr_dict=GR[next][i]['attr_dict'])
# f = open('netGraph3', 'wb')
# pickle.dump(G, f)
# f.close()
# def k_shortest_paths(graph, src, dst, k=1):
#     generator = nx.shortest_simple_paths(graph, source=src,
#                                              target=dst)
#     shortest_paths = []
#     try:
#         for path in generator:
#             if k <= 0:
#                 break
#             shortest_paths.append(path)
#             k -= 1
#         return shortest_paths
#     except:
#         print("No path between %s and %s" % (src, dst))
# base='10.0.0.{}'
# all_paths= {}
#
# for i in range(1,17):
#     for j in range(1,17):
#         if i==j :
#             continue
#         else:
#             source=base.format(i)
#             dst=base.format(j)
#             all_paths[(source,dst)]=nx.shortest_path(G,source,dst)
# # pprint(all_paths[('10.0.0.1', '10.0.0.4')])
# paths = eval(open('paths3', 'r').read())
# # pprint(paths[('10.0.0.1', '10.0.0.4')])
# sum=0
# TableNum ={}
# for i in range(1,17):
#     num=all_paths.__str__().count(' {},'.format(i))
#     sum+=num
#     print(i,': ',num)
#     TableNum[i]=round(num/816*547/5)
# print(TableNum)


t= {1:1, 2:3}
for k,v in t.items():
    print(k,v)
sys.exit(0)

with  open('paths3.json','w') as f:
    f.write(all_paths.__str__())
# for node in G.nodes():
#     print(node,end=': ')
#     for neigh in G.neighbors(node):
#         print(neigh,end=', ')
#     print()



data = 'yuegengbiaogregaaaaaaaaaaaaaaaaaaaaaaaaaa' \
       'greagggggggggggggggggggggggggggggg' \
       'greaaaaaaaaaaaaaaaaaaaaaaaaaaaaggg' \
       'greaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' * 9
# ip_src='10.0.0.1'
# ip_dst='10.0.0.2'
# tcp_srcp=12324
# tcp_dstp=1234
# pkt=Ether()/IP(src=ip_src,dst=ip_dst,flags=2,id=RandShort())/TCP(sport=tcp_srcp,dport=tcp_dstp)/data
# print(sendpfast(pkt,iface='h1-eth0',pps=10, loop=200,parse_results=1))
TableNum = {1: 6, 2: 5, 3: 6, 4: 5, 5: 6, 6: 12, 7: 12, 8: 9, 9: 5, 10: 9, 11: 8, 12: 8, 13: 8, 14: 6, 15: 5, 16: 4}
for k in TableNum:
    TableNum[k] += 2
print(TableNum)

TableNum = {1: 27, 2: 20, 3: 28, 4: 21, 5: 29, 6: 45, 7: 44, 8: 42, 9: 22, 10: 35, 11: 33, 12: 29, 13: 28, 14: 27,
            15: 21, 16: 10}
switchF = [42, 36, 45, 33, 40, 84, 83, 67, 32, 62, 59, 60, 56, 44, 35, 30]

switchFG = {}
sw = 1
for i in switchF:
    switchFG[sw] = (round(i / sum(switchF) * 268.8 / 5))
    sw += 1
print(switchFG)
print(sum(switchFG.values()))
print(80 / 5 * 3.36)

sys.exit(0)


class myThread(threading.Thread):
    def __init__(self, local):
        threading.Thread.__init__(self)
        np.random.seed(local)

    def run(self):
        for i in range(5):
            print('[', np.random.randint(1, 17), ',', np.random.poisson(700), ']', end=' ')
        print()


start = time.time()
for i in range(10, 161):
    np.random.seed(i)
    print(np.random.randint(0, 2), end=' ')
    if i % 10 == 9:
        print()
    # local=i
    # myThread(local).start()
    # time.sleep(0.5)
