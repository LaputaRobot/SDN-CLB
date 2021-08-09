#!/usr/bin/python3
import time
import math
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController,OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink,Link
from mininet.topo import Topo


class MyTopo(Topo):
    "Simple topology example."
    def __init__(self,**opts):
        Topo.__init__(self,**opts)
        switches=[]
        switches.append('s0')
        for i in range(1,17):
            h=self.addHost('h%s'%(i),ip='10.0.0.%s'%(i))
            s=self.addSwitch('s%s'%(i))
            switches.append(s)
            self.addLink(h,s)
        linkopts=dict(bw=10)
        for i in range(1, 17):
            for j in range(1, 3):
                next = i + j
                if next > 16:
                    next -= 16
                self.addLink(switches[i],switches[next],**linkopts)


def pingClient(net):
    clients= {}
    for i in range(1,17):
        clients['h%d'%i]=net.get('h%d'%i)
        host=clients['h%d'%i]
        if i==1:
            host.cmd('ping 10.0.0.{} -c1'.format(i+1))
            print('h{} ping 10.0.0.{} -c1'.format(i,i+1))
        else:
            host.cmd('ping 10.0.0.1 -c1')
            print('h{} ping 10.0.0.1 -c1'.format(i))

def runClient(net):
    clients= {}
    for i in range(1,17):
        clients['h%d' % i] = net.get('h%d' % i)
        host = clients['h%d' % i]
        host.cmd('iperf -s -u &')
        print("run iperf server at 10.0.0.{}".format(i))
        # if (math.ceil(i/4)==1 or math.ceil(i/4)==3):
        #     host.cmd('/home/ygb/ESMLB/Ryu-venv/bin/python3 iperf4.py {} &'.format(i))
        #     print('run iperf client at 10.0.0.{} '.format(i))
        #     print('ok')
        host.cmd('/home/ygb/ESMLB/Ryu-venv/bin/python3 iperf4.py {} &'.format(i))
        print('run iperf client at 10.0.0.{} '.format(i))
        print('ok')


def runScapy(net):
    for i in range(1, 17):
        host = net.get('h%d' % i)
        host.cmd('sudo python3 -u scapyTraffic.py {} >scapy{}.log&'.format(i, i))
        print('run scapy at 10.0.0.{} '.format(i))


REMOTE_CONTROLLER_IP = '0.0.0.0'
# REMOTE_CONTROLLER_IP='192.168.136.1'
if __name__ == '__main__':
    setLogLevel('info')
    topo = MyTopo()
    net = Mininet(topo=topo, controller=None, link=TCLink, switch=OVSKernelSwitch)
    net.addController("c0",
                      controller=RemoteController,
                      ip=REMOTE_CONTROLLER_IP,
                      port=6653)
    net.addController("c1",
                      controller=RemoteController,
                      ip=REMOTE_CONTROLLER_IP,
                      port=6654)
    net.addController("c2",
                      controller=RemoteController,
                      ip=REMOTE_CONTROLLER_IP,
                      port=6655)
    net.addController("c3",
                      controller=RemoteController,
                      ip=REMOTE_CONTROLLER_IP,
                      port=6656)
    net.start()
    print('net started')
    pingClient(net)
    net.pingAll()
    initedConNum = 0
    while initedConNum != 4:
        f = open('/home/ygb/ESMLB/ryu/app/otherApp/initedController', 'r')
        lines = f.readlines()
        initedConNum = len(lines)
        f.close()
        time.sleep(1)
    # print('will runClient')
    # runClient(net)

    print('will runScapy')
    runScapy(net)
    CLI(net)
    net.stop()
