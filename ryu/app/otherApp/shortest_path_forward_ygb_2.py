import logging
import traceback

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology.api import get_switch, get_link
from ryu.topology import event
from ryu.lib.packet import packet, tcp, udp
from ryu.lib.packet import ethernet, ether_types, arp, ipv4
from ryu.lib import hub

import networkx as nx
import time
import socket
import queue
import my_load_balancer
import json
import math
import pickle
import os
import TOPSIS
import pandas as pd
import lock

# TableNum={1: 6, 2: 3, 3: 6, 4: 4, 5: 7, 6: 11, 7: 10, 8: 13, 9: 6, 10: 7, 11: 6, 12: 7, 13: 7, 14: 6, 15: 5, 16: 2}
# TableNum={1: 28, 2: 24, 3: 30, 4: 22, 5: 27, 6: 56, 7: 56, 8: 45, 9: 22, 10: 42, 11: 40, 12: 40, 13: 38, 14: 30, 15: 24, 16: 20}
TableNum = {1: 6, 2: 5, 3: 6, 4: 5, 5: 6, 6: 12, 7: 12, 8: 9, 9: 5, 10: 9, 11: 8, 12: 8, 13: 8, 14: 6, 15: 5, 16: 4}
# TableNum={1: 3, 2: 2, 3: 3, 4: 2, 5: 3, 6: 6, 7: 6, 8: 4, 9: 2, 10: 4, 11: 4, 12: 4, 13: 4, 14: 3, 15: 2, 16: 2}
for k in TableNum:
    TableNum[k] = 7 + 2


#
class PathForward(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PathForward, self).__init__(*args, **kwargs)
        self.G = None
        self.paths = {}
        self.hasPaths = False
        self.sendPath = False
        # 作为get_switch()和get_link()方法的参数传入
        self.topology_api_app = self
        #
        self.controllerId = 1

        self.datapaths = {}
        self.initRole = False
        self.initedSWNum = 0  # 分配交换机时，本控制器已经初始化的交换机数量
        self.initedConNum = 1  # 已经初始化的控制器数量
        self.initCon = 0
        self.startTime = time.time()
        self.canMig = False
        # print('开始于：{}'.format(self.startTime))

        # 控制器通信相关
        self.send_queue = hub.Queue(16)
        self.socket = socket.socket()
        self.start_serve('127.0.0.1', 8888)
        print('start_serve')

        # 运行监控线程
        self.monitor_thread = hub.spawn(self._monitor)
        self.get_Table_Num = hub.spawn(self._getTableNum)  # 监控交换机的流表信息

        self.lastMonitorTime = time.time()
        self.localDatapathsRate = {}
        self.myLoad = 0
        self.myLoadWin = []
        self.respondTime = 0

        self.otherRAM = {}
        # self.get_Ram = hub.spawn(self._getRam)

        self.dpFlowTableNum = {}  # 交换机的流表数
        self.selfFTPlus = False

        # barrier相关
        self.barrier_reply_Count = 0
        # 迁移过程变量
        self.minRate=1000
        self.startMigration = False  # 开始迁移的标志
        self.deleteFlag = False  # 本地控制器收到删除流表的标志
        self.otherDel = False  # 目标控制器删除流表的标志
        self.dstMaster = False  # 目标控制器请求到Master成功的标志

        self.endMigration = False  # 结束迁移
        self.requestControllerID = 0  # 请求迁移的控制器
        self.requestDatapaths = []  # 请求迁移的交换机列表
        self.fromController = False
        self.toController = False
        self.cachePacketIn = queue.Queue()

        # 迁移间隔
        self.lastMigTime = time.time()

    def _monitor(self):
        """
        初始化，并监控交换机，超载则发送交换机迁移信息
        """
        while True:
            # print("start monitor at {}".format(time.time()))
            if not self.initRole and self.sendPath and self.initCon == 0:
                print('分配交换机')
                for i in range(1, 17):
                    dpConNum = math.ceil(i / 4)
                    dp = self.datapaths[i]
                    if self.controllerId == dpConNum:
                        self.send_role_request(dp, ofproto_v1_3.OFPCR_ROLE_MASTER)
                        self.localDatapathsRate.setdefault(i, {})
                        numDict = {'num': 0,
                                   'smallNum': 0,
                                   'zeroNum': 0,
                                   'minInPort': 0,
                                   'srcIP': 0,
                                   'dstIP': 0,
                                   'minTpPort': -1,
                                   'minPacketRate': 100}
                        self.dpFlowTableNum[i] = numDict
                    else:
                        self.send_role_request(dp, ofproto_v1_3.OFPCR_ROLE_SLAVE)

                self.initCon = self.initCon + 1
                myport = str(self.controllerId + 6652)
                # 使用cpugroup对控制器的CPU处理能力进行限制
                print('cgroup to limit controller cpu')
                result = os.popen('ps -ef|grep ryu-manager').readlines()
                for r in result:
                    if myport in r:
                        process = r.split()[1]
                        print(process)
                        os.system('echo {} |sudo tee /sys/fs/cgroup/cpu/controller{}/tasks'.format(process,
                                                                                                   self.controllerId))

                self.del_Flow_Data = hub.spawn(self._delFlowData)  # 删除未安装流表，且流速率为0的流的统计信息

            if self.initedConNum != 4:
                f = open('initedController', 'r')
                lines = f.readlines()
                self.initedConNum = len(lines)
                f.close()

            if self.initRole and self.initedConNum == 4:
                # print('进入监控 at {}'.format(time.time()))
                for dpId in self.localDatapathsRate.keys():
                    for flow in self.localDatapathsRate[dpId].keys():
                        delta = self.localDatapathsRate[dpId][flow]['packetInCount'] - \
                                self.localDatapathsRate[dpId][flow]['lastPacketInCount']
                        self.localDatapathsRate[dpId][flow]['lastPacketInCount'] = self.localDatapathsRate[dpId][flow][
                            'packetInCount']
                        thisRate = delta / (time.time() - self.lastMonitorTime)

                        if len(self.localDatapathsRate[dpId][flow]['packetInRateWind']) >= 2:
                            self.localDatapathsRate[dpId][flow]['packetInRateWind'].pop(0)
                            self.localDatapathsRate[dpId][flow]['packetInRateWind'].append(thisRate)
                        else:
                            self.localDatapathsRate[dpId][flow]['packetInRateWind'].append(thisRate)
                        packetInRate = sum(
                            self.localDatapathsRate[dpId][flow]['packetInRateWind']) / len(
                            self.localDatapathsRate[dpId][flow]['packetInRateWind'])
                        self.localDatapathsRate[dpId][flow]['packetInRate'] = packetInRate
                        # self.localDatapathsRate[dpId][flow]['packetInRate'] = thisRate
                # print('结束各流负载计算at {}'.format(time.time()))
                self.lastMonitorTime = time.time()
                rateData = {self.controllerId: self.localDatapathsRate}

                # print('写入：{}'.format(fileData))
                if self.myFile:
                    self.myFile.seek(0)
                    self.myFile.truncate()
                    self.myFile.write(json.dumps(rateData))
                    self.myFile.flush()
                    # print('完成写入：at {}'.format(time.time()))

                flowTableData = {self.controllerId: self.dpFlowTableNum}
                if self.myFlowTableFile:
                    self.myFlowTableFile.seek(0)
                    self.myFlowTableFile.truncate()
                    self.myFlowTableFile.write(json.dumps(flowTableData))
                    self.myFlowTableFile.flush()
                    # print('完成写入：at {}'.format(time.time()))

                thisMyLoad = 0
                otherLoads = {}
                details = {}
                for dpid in self.localDatapathsRate.keys():
                    details[dpid] = {}
                    bigNum = 0
                    smallNum = 0
                    details[dpid]['rate'] = 0
                    for flow in self.localDatapathsRate[dpid].keys():
                        # flow_port = flow.split(',')[-2][1:]
                        # if flow_port in details[dpid]:
                        #     flow_port += '--'
                        # details[dpid][flow_port] =
                        details[dpid]['rate'] += self.localDatapathsRate[dpid][flow]['packetInRate']
                        if self.localDatapathsRate[dpid][flow]['packetInRate'] != 0:
                            if self.localDatapathsRate[dpid][flow]['packetInRate'] > 4:
                                bigNum += 1
                            else:
                                smallNum += 1
                        # if self.localDatapathsRate[dpid][flow]['packetInRate'] > 4 and self.dpFlowTableNum[dpid][
                        #     'smallNum'] > 0:
                        #     continue

                    details[dpid]['bigNum'] = bigNum
                    details[dpid]['smallNum'] = smallNum
                    if details[dpid]['bigNum']>self.dpFlowTableNum[dpid]['smallNum']> 0:
                        details[dpid]['bigNum'] -= self.dpFlowTableNum[dpid]['smallNum']
                        details[dpid]['rate']-=self.dpFlowTableNum[dpid]['smallNum']*10
                    elif self.dpFlowTableNum[dpid]['smallNum']>details[dpid]['bigNum']>0:
                        details[dpid]['rate'] -=details[dpid]['bigNum']*10
                        details[dpid]['bigNum']=0
                    thisMyLoad += details[dpid]['rate']

                # if len(self.myLoadWin) < 2:
                #     self.myLoadWin.append(thisMyLoad)
                # else:
                #     self.myLoadWin.pop(0)
                #     self.myLoadWin.append(thisMyLoad)
                #
                # self.myLoad = sum(self.myLoadWin) / len(self.myLoadWin)
                self.myLoad=thisMyLoad

                otherConFT = {}
                for other in self.flowTableFiles:
                    other.seek(0)
                    try:
                        data = json.load(other)
                        # print('get otherConFT',data)
                        otherController = 0
                        for controller in data.keys():
                            otherController = controller
                        otherConFT[otherController] = data[otherController]
                    except Exception as e:
                        traceback.print_exc()
                        print(e)


                for other in self.files:
                    other.seek(0)
                    try:
                        data = json.load(other)
                        otherController = 0
                        otherControllerLoad = 0
                        for controller in data.keys():
                            load = 0
                            # print('controller' + controller + '--------', end=' ')
                            otherController = controller
                            for switch in data[controller]:
                                big=0
                                for flow in data[controller][switch]:
                                    if data[controller][switch][flow]['packetInRate'] > 4 :
                                        big+=1
                                    load = load + data[controller][switch][flow]['packetInRate']
                                load-=min(big,otherConFT[controller][switch]['smallNum'])*10
                                # print('switch' + switch + ': ', data[controller][switch]['packetInRate'], end='   ')
                            otherControllerLoad = load
                        otherLoads[otherController] = otherControllerLoad
                    except json.JSONDecodeError as e:
                        print(e)

                otherConSZ = {}
                for con in otherConFT:
                    otherConSZ[int(con)] = 0
                    for sw in otherConFT[con]:
                        otherConSZ[int(con)] += (otherConFT[con][sw]["smallNum"] + otherConFT[con][sw]["zeroNum"])

                avgLoad = (self.myLoad + sum(otherLoads.values())) / 4
                LBR = 0
                if avgLoad != 0:
                    LBR = 1 - (abs(self.myLoad - avgLoad) + sum(abs(v - avgLoad) for v in otherLoads.values())) / (
                            4 * avgLoad)
                print('myLoad: ', self.myLoad)
                # print('thisLoad ', thisMyLoad)
                print('details:', details)
                print('Table Num: ', self.dpFlowTableNum)
                # print('detail:', self.localDatapathsRate)
                print('otherLoads: ', otherLoads)
                # print('otherConSZ: ', otherConSZ)
                # print('otherConFT: ', otherConFT)
                # print('respondTime: ', self.respondTime)
                # print('LBR: ', LBR)

                self.respondTimelogger.info(
                    "{},{},{},{},{},{},{},{}".format(time.time(), self.respondTime, self.myLoad, thisMyLoad, LBR,
                                                     self.controllerId,
                                                     otherLoads, avgLoad * 4))
                # dpIdList=list(self.dpFlowTableNum.keys())
                # self.respondTimelogger.info('{},{},{},{},{},{},{},{}'.format(dpIdList[0],self.dpFlowTableNum[dpIdList[0]]['num'],
                #                                                              dpIdList[1],self.dpFlowTableNum[dpIdList[1]]['num'],
                #                                                              dpIdList[2],self.dpFlowTableNum[dpIdList[2]]['num'],
                #                                                              dpIdList[3],self.dpFlowTableNum[dpIdList[3]]['num'],
                #                                                              ))
                self.respondTime = 0  # 重置响应时间

                allLoads = otherLoads.copy()
                allLoads[self.controllerId.__str__()] = self.myLoad
                maxL = 0
                maxC = 0
                minL = 10000
                minC = 0
                for k, v in allLoads.items():
                    if v < minL:
                        minC = k
                        minL = v
                    if v > maxL:
                        maxC = k
                        maxL = v
                # print(maxC,maxL,minC,minL)
                threshold = 40

                if not self.canMig and maxL > 150:
                    print('can migration')
                    self.canMig = True

                if self.canMig and maxL - minL > threshold and time.time() - self.lastMigTime > 2 and self.controllerId.__str__() == maxC and not self.startMigration and len(
                        otherLoads.keys()) == 3 and lock.get_lock(True):
                    # if self.canMig and self.myLoad>150 and self.myLoad>avgLoad and not self.startMigration and len(otherLoads.keys()) == 3 and lock.get_lock(True):
                    # 发现超载，向目标控制器发送迁移请求
                    # datapathId = 0
                    # self.minRate = 10000
                    # for switch in self.localDatapathsRate.keys():
                    #     if  self.dpFlowTableNum[switch]['smallNum']==0 and details[switch]['bigNum']>0:
                    #         dpRate = 0
                    #         for flow in self.localDatapathsRate[switch].keys():
                    #             dpRate += self.localDatapathsRate[switch][flow]['packetInRate']
                    #         if dpRate < self.minRate:
                    #             datapathId = switch
                    #             self.minRate = dpRate

                        # datapathId=self.localDatapathsRate.keys()[0]

                    # otherControllerId = []
                    # for i in range(1, 5):
                    #     if i != self.controllerId:
                    #         otherControllerId.append(i)
                    # start = time.time()
                    # otherHop = TOPSIS.getOtherHop(str(datapathId), str(self.controllerId))
                    # # dataD = {'CPU': [v + 0.1 for v in otherLoads.values()], 'SZN': [v for v in otherConSZ],
                    # #          'hop': [v for v in otherHop.values()]}
                    # dataD = {'CPU': [v + 0.1 for v in otherLoads.values()], 'RAM': [1, 1, 1],
                    #          'hop': [1,1,1]}
                    # index = [k for k in otherHop.keys()]
                    # data = pd.DataFrame(dataD, index=index)
                    # data['CPU'] = 1 / data['CPU']
                    # data['RAM'] = 1 / data['RAM']
                    # data['hop'] = 1 / data['hop']
                    # print('time spend at get data:', time.time() - start)
                    # self.dstController = int(TOPSIS.esmlb(data, TOPSIS.WEIGHT))
                    all_choices=self.get_all_choice(otherLoads,details,avgLoad)
                    print('all choices: ',all_choices)
                    datapathId=all_choices[0][0]
                    self.dstController = int(all_choices[0][1])
                    # self.dstController = int(minC)
                    # if otherLoads[self.dstController.__str__()] + self.minRate > self.myLoad:
                    #     print('dst con will be overloaded too')
                    #     lock.write_lock()
                    #     continue



                    message = json.dumps({'srcController': self.controllerId,
                                          'dstController': self.dstController, 'startMigration': 'True',
                                          'datapath': datapathId
                                          })
                    self.send(message)

            hub.sleep(1)

    def get_all_choice(self,otherLoads,details,avg):
        choices=[]
        for dpid in details:
            for con in otherLoads:
                if otherLoads[con]+details[dpid]['rate']<avg:
                    choices.append([dpid,con])
        return choices

    def get_best_choice(self,choices,otherConFT):
        for dpid,con in choices.items():
            for sw in otherConFT[con]:
                if otherConFT[con][sw]["smallNum"]==0 :
                    pass



    def _delFlowData(self):
        # 删除过期的流表数据
        while True:
            try:
                print('del flow data')
                for dpID in self.localDatapathsRate:
                    popKey = []
                    for flow in self.localDatapathsRate[dpID]:
                        if len(self.localDatapathsRate[dpID][flow]['packetInRateWind']) >= 1:
                            packetInRate = sum(
                                self.localDatapathsRate[dpID][flow]['packetInRateWind']) / len(
                                self.localDatapathsRate[dpID][flow]['packetInRateWind'])
                            if packetInRate == 0:
                                # print('del flow data: ', flow)
                                popKey.append(flow)

                    for k in popKey:
                        self.localDatapathsRate[dpID].pop(k)

                time.sleep(5)
            except Exception as e:
                traceback.print_exc()
                print(e)

    def _getTableNum(self):
        while True:
            try:
                if self.initRole and self.initedConNum == 4 and self.startMigration != True:
                    # start=time.time()
                    for dp_id in self.dpFlowTableNum.keys():
                        numDict = eval(open('sw{}FT.json'.format(dp_id), 'r').read())
                        # print('switch {}, flow table message {}'.format(dp_id, numDict))
                        # 如果期间控制器直接安装流表，使得流表数增加，则
                        if self.selfFTPlus == True and self.dpFlowTableNum[dp_id]["num"] > numDict["num"]:
                            numDict["num"] = self.dpFlowTableNum[dp_id]["num"]
                        self.dpFlowTableNum[dp_id] = numDict
                        # print('get switch {} flow table num spend {}'.format(dp_id,time.time() - start))
                        # start=time.time()
                    self.selfFTPlus = False
                time.sleep(1)
            except Exception as e:
                traceback.print_exc()
                print(e)

    def _getRam(self):
        while True:
            self.otherRAM = TOPSIS.getRAM(self.controllerId)

    def openFile(self):
        self.files = []
        self.myFile = open('con{}Rate.json'.format(self.controllerId), 'w')
        self.myFile.write(json.dumps(self.localDatapathsRate))
        self.myFile.flush()
        for i in range(1, 5):
            if i != self.controllerId:
                self.files.append(open("con{}Rate.json".format(i), 'r'))

    def openFTFile(self):
        self.flowTableFiles = []
        self.myFlowTableFile = open('con{}FT.json'.format(self.controllerId), 'w')
        self.myFlowTableFile.write(json.dumps(self.dpFlowTableNum))
        self.myFlowTableFile.flush()
        for i in range(1, 5):
            if i != self.controllerId:
                self.flowTableFiles.append(open("con{}FT.json".format(i), 'r'))

    def start_serve(self, server_addr, server_port):
        """
        开启Socket通信
        """
        try:
            self.socket.connect((server_addr, server_port))
            self.status = True
            hub.spawn(self._rece_loop)
            hub.spawn(self._send_loop)
        except Exception as e:
            raise e

    def send(self, msg):
        """
        将消息放到消息队列，以供发送
        """
        if self.send_queue != None:
            self.send_queue.put(msg)

    def _send_loop(self):
        """
        监控消息队列，如果有消息，则发送出去
        """
        # print('self._send_loop()')
        try:
            while self.status:
                message = self.send_queue.get()
                message += '\n'
                print('send message {} at: {}'.format(message, time.time()))
                # print(message)
                self.socket.sendall(message.encode('utf-8'))
        finally:
            self.send_queue = None

    def _rece_loop(self):
        """
        控制器接收消息，并分析消息类型，以作进一步处理
        """
        while self.status:
            try:
                message = self.socket.recv(128)
                message = message.decode('utf-8')
                # print('receive msg1:',message)
                if len(message) == 0:  # 关闭连接
                    self.logger.info('connection fail, close')
                    self.status = False
                    break
                while '\n' != message[-1]:
                    message += self.socket.recv(128).decode('utf-8')
                print('receive msg:', message)
                msg = message.split('\n')
                for m in msg:
                    if m != '':
                        messageDict = eval(m)
                        # print('receive msg at:',time.time())

                        if 'sendPath' in messageDict.keys():
                            print('get paths ...............')
                            self.paths = eval(messageDict['paths'])
                            f = open('netGraph', 'rb')
                            self.G = pickle.load(f)
                            self.hasPaths = True
                            self.sendPath = True

                        if 'startMigration' in messageDict.keys():
                            print('receive migration request at:', time.time())
                            print('receive msg {} from {}:'.format(message, messageDict['srcController']))
                            if messageDict['startMigration'] == 'True' and not self.startMigration and time.time()-self.lastMigTime>2:
                                # 收到迁移请求，请求角色到EQUAL
                                self.startMigration = True  # 目标控制器的开始迁移标志变为TRUE，防止同时出现多个控制器迁移到相同的控制器，而发生冲突
                                self.toController = True
                                # self.file.write('{},{}'.format(time.time(), '请求到EQUAL'))
                                # self.file.flush()
                                self.requestControllerID = messageDict['srcController']
                                print('request to equal')
                                # TO DO：
                                # 将交换机换成列表的形式
                                dp = self.datapaths[messageDict['datapath']]
                                self.requestDatapaths.append(dp)
                                self.respondTimelogger.info(
                                    '{},dst controller receive mig request at switch {} from controller {}'.format(
                                        time.time(),
                                        messageDict['datapath'],
                                        self.requestControllerID))
                                # ofp_parse=dp.ofproto_parser
                                ofp = dp.ofproto
                                self.send_role_request(dp, ofp.OFPCR_ROLE_EQUAL)
                            else:
                                readyMessage = json.dumps({'srcController': self.controllerId,
                                                           'dstController': messageDict['srcController'],
                                                           'ready': 'False', "datapath": messageDict['datapath']})
                                self.send(readyMessage)


                        if 'ready' in messageDict.keys():  #
                            if messageDict['ready'] == 'True':
                                # 安装空流表，发送barrier消息
                                dpid=messageDict['datapath']
                                dp = self.datapaths[dpid]
                                self.requestDatapaths.append(dp)
                                self.startMigration = True
                                self.fromController = True
                                self.requestControllerID = self.controllerId
                                # self.requestDatapaths.append(self.datapaths[2])
                                print('find overload at ', time.time())
                                print('迁移交换机：S{}, Rate is {}, Table is {}'.format(dpid, self.minRate,
                                                                                  self.dpFlowTableNum[dpid]))
                                self.respondTimelogger.info(
                                    '{},migration switch{} Rate {} from {} to {}'.format(
                                        time.time(),
                                        dpid,
                                        self.minRate,
                                        self.controllerId,
                                        self.dstController))
                                self.migInterLogger.info(
                                    '{},migration switch{},Rate {}, from {}, to {},{},{}'.format(time.time(),
                                                                                                 dpid, self.minRate,
                                                                                                 self.controllerId,
                                                                                                 self.dstController,
                                                                                                 self.lastMigTime,
                                                                                                 time.time() - self.lastMigTime))
                                self.lastMigTime = time.time()

                                ofp_parse = dp.ofproto_parser
                                ofp = dp.ofproto
                                # self.send_role_request(dp, ofp.OFPCR_ROLE_EQUAL)
                                out_port = 1234
                                in_port = 1234
                                actions = [ofp_parse.OFPActionOutput(out_port)]
                                match = ofp_parse.OFPMatch(in_port=in_port)
                                flags = ofp.OFPFF_SEND_FLOW_REM
                                self.add_flow1(dp, 1, match, actions, idle_timeout=0, flags=flags)
                                self.barrier_reply_Count = 0
                                self.send_barrier_request(dp)
                                print('安装空流表，发送barrier消息 at {}'.format(time.time()))
                            if messageDict['ready']=='False':
                                self.respondTimelogger.info('Fail to request mig, because dst controller just mig '
                                                            'a few time ago')
                                lock.write_lock()
                                continue


                        if 'delFlowTable' in messageDict.keys():
                            if messageDict['delFlowTable'] == 'True':
                                self.otherDel = True

                        if 'sendFlowData' in messageDict.keys():
                            self.localDatapathsRate[self.requestDatapaths[0].id] = messageDict['FlowData']

                        if 'cmd' in messageDict.keys():
                            if messageDict['cmd'] == 'set_id':
                                self.controllerId = messageDict['client_id']
                                self.resultFolder = messageDict['resultFolder']
                                print('get controller id {}'.format(self.controllerId))
                                if self.controllerId == 1:
                                    self.hasPaths = True
                                self.openFile()
                                self.openFTFile()
                                self.respondTimelogger = logging.getLogger('respondTime')
                                self.respondTimelogger.setLevel(level=logging.DEBUG)
                                self.respondTimehandler = logging.FileHandler(self.resultFolder + '/' +
                                                                              'respondTime{}.csv'.format(
                                                                                  self.controllerId),
                                                                              encoding='UTF-8')
                                self.respondTimelogger.addHandler(self.respondTimehandler)

                                self.migInterLogger = logging.getLogger('migInter')
                                self.migInterLogger.setLevel(level=logging.DEBUG)
                                self.migInterHandler = logging.FileHandler(self.resultFolder + '/' + 'migInter.csv',
                                                                           encoding='UTF-8')
                                self.migInterLogger.addHandler(self.migInterHandler)

                        if 'endMigration' in messageDict.keys():
                            if messageDict['endMigration'] == 'True':
                                self.endMigration = True
                                # self.file.write('{},{}'.format(time.time(), '结束迁移'))
                                # self.file.flush()
                                print('收到结束迁移于：', time.time())
                                dpid = messageDict['datapath']
                                dp = self.datapaths[dpid]
                                ofp = dp.ofproto
                                print('请求到MASTER')
                                self.send_role_request(dp, ofp.OFPCR_ROLE_MASTER)
                                # print('迁移后获取各交换机流表')
                                # self.getTableNum(dpid)
                                print('处理缓存的消息')
                                while not self.cachePacketIn.empty():
                                    ev = self.cachePacketIn.get()
                                    self.cache_packet_in_handler(ev)
                                print('处理完成，结束迁移')

                        if 'slave' in messageDict.keys():
                            if messageDict['slave'] == 'True':
                                while self.dstMaster != True:
                                    time.sleep(0.001)
                                print('receive slave msg from source controller')
                                lock.write_lock()
                                self.respondTimelogger.info('{},end migration'.format(time.time()))
                                # self.requestDatapaths.remove(dp)
                                self.fromController = False
                                self.toController = False
                                self.startMigration = False  # 开始迁移的标志
                                self.deleteFlag = False  # 收到删除流表的标志
                                self.endMigration = False  # 结束迁移
                                self.requestControllerID = 0  # 请求迁移的控制器
                                self.requestDatapaths = []

            except ValueError:
                print(('Value error for %s, len: %d', message, len(message)))

    # 添加流表项的方法
    def add_flow(self, datapath, priority, match, actions):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        command = ofp.OFPFC_ADD
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        req = ofp_parser.OFPFlowMod(datapath=datapath, command=command,
                                    priority=priority, match=match, instructions=inst)
        datapath.send_msg(req)

    def del_flow(self, datapath, match):
        ofp = datapath.ofproto
        parser = datapath.ofproto_parser
        cookie = cookie_mask = 0
        table_id = 0
        idle_timeout = 0
        hard_timeout = 0
        priority = 1
        buffer_id = ofp.OFP_NO_BUFFER
        match = parser.OFPMatch(in_port=1234)
        actions = []
        inst = []
        req = parser.OFPFlowMod(datapath, cookie, cookie_mask,
                                table_id, ofp.OFPFC_DELETE,
                                idle_timeout, hard_timeout,
                                priority, buffer_id,
                                1234, ofp.OFPG_ANY,
                                ofp.OFPFF_SEND_FLOW_REM,
                                match, inst)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        print('flow removed ............at time:{}, switch {}'.format(time.time(), dp.id))
        if msg.reason == ofp.OFPRR_IDLE_TIMEOUT:
            reason = 'IDLE TIMEOUT'
        elif msg.reason == ofp.OFPRR_HARD_TIMEOUT:
            reason = 'HARD TIMEOUT'
        elif msg.reason == ofp.OFPRR_DELETE:
            reason = 'DELETE'
            if self.startMigration == True:
                if self.toController == True:
                    self.deleteFlag = True
                    # self.localDatapaths[dp.id] = dp
                    self.localDatapathsRate.setdefault(dp.id, {})
                    # self.localDatapathsRate[dp.id]['lastPacketInCount'] = 0
                    # self.localDatapathsRate[dp.id]['packetInCount'] = 0
                    # self.localDatapathsRate[dp.id]['packetInRate'] = 0
                    # self.localDatapathsRate[dp.id]['packetInRateWind'] = []
                    numDict = {'num': 100,
                               'smallNum': 0,
                               'zeroNum': 0,
                               'minInPort': 0,
                               'srcIP': 0,
                               'dstIP': 0,
                               'minTpPort': -1,
                               'minPacketRate': 100}
                    self.dpFlowTableNum[dp.id] = numDict
                    delMsg = json.dumps({'srcController': self.controllerId,
                                         'dstController': self.requestControllerID,
                                         'delFlowTable': 'True', "datapath": dp.id})
                    self.send(delMsg)

                if self.fromController == True:
                    # self.file.write('{},{}\n'.format(time.time(), '已删除空流表'))
                    # self.file.flush()
                    while self.otherDel != True:
                        time.sleep(0.05)
                    self.deleteFlag = True
                    message = json.dumps({'srcController': self.controllerId,
                                          'dstController': self.dstController,
                                          'sendFlowData': 'True', "FlowData": self.localDatapathsRate[dp.id]})
                    self.send(message)
                    print('本控制器流表删除状态：{}, 其他控制器删除状态：{}'.format(self.deleteFlag, self.otherDel))
                    print('流表已删除，进入backout......at ', time.time())
                    self.send_barrier_request(dp)
                # time.sleep(5.310)
                # self.deleteFlag=False
                # print('结束迁移 at',time.time())
                # endMigrationMsg=json.dumps({'dstController':2,'endMigration':'True','datapath':dp.id})
                # self.send(endMigrationMsg)
                # print('请求为SLAVE')
                # self.send_role_request(dp,ofp.OFPCR_ROLE_SLAVE)
        elif msg.reason == ofp.OFPRR_GROUP_DELETE:
            reason = 'GROUP DELETE'
        else:
            reason = 'unknown'
        print('OFPFlowRemoved received: '
              'cookie=%d priority=%d reason=%s table_id=%d '
              'duration_sec=%d duration_nsec=%d '
              'idle_timeout=%d hard_timeout=%d '
              'packet_count=%d byte_count=%d match.fields=%s' % (
                  msg.cookie, msg.priority, reason, msg.table_id,
                  msg.duration_sec, msg.duration_nsec,
                  msg.idle_timeout, msg.hard_timeout,
                  msg.packet_count, msg.byte_count, msg.match))

    def send_role_request(self, datapath, role):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        gen_id = my_load_balancer.get_gen_id(ofp, role)
        print('get gen_id:{}'.format(gen_id))
        req = ofp_parser.OFPRoleRequest(datapath, role, gen_id)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPErrorMsg,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        if dp in self.requestDatapaths and self.fromController == True and \
                msg.type == ofproto_v1_3.OFPET_ROLE_REQUEST_FAILED and \
                msg.code == ofproto_v1_3.OFPRRFC_STALE:
            self.send_role_request(dp, ofproto_v1_3.OFPCR_ROLE_SLAVE)
            print('重新请求至SLAVE')
        if dp in self.requestDatapaths and self.toController == True and \
                msg.type == ofproto_v1_3.OFPET_ROLE_REQUEST_FAILED and \
                msg.code == ofproto_v1_3.OFPRRFC_STALE:
            self.send_role_request(dp, ofproto_v1_3.OFPCR_ROLE_MASTER)
            print('重新请求至MASTER')

        self.logger.debug('OFPErrorMsg received: type=0x%02x code=0x%02x ',
                          msg.type, msg.code)

    @set_ev_cls(ofp_event.EventOFPRoleReply, MAIN_DISPATCHER)
    def role_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id
        ofp = dp.ofproto
        if msg.role == ofp.OFPCR_ROLE_NOCHANGE:
            role = 'NOCHANGE'
        elif msg.role == ofp.OFPCR_ROLE_EQUAL:
            role = 'EQUAL'
            if dp in self.requestDatapaths:
                # dstController=self.requestControllerID
                readyMessage = json.dumps({'srcController': self.controllerId,
                                           'dstController': self.requestControllerID,
                                           'ready': 'True', "datapath": dpid})
                self.send(readyMessage)
                print('请求到EQUAL')
        elif msg.role == ofp.OFPCR_ROLE_MASTER:
            role = 'MASTER'
            if not self.initRole:
                self.initedSWNum = self.initedSWNum + 1
                if self.initedSWNum == 16:
                    print('controller {}  initialized at {}'.format(self.controllerId, time.time()))
                    f = open('initedController', 'a+')
                    f.write(str(self.controllerId) + '\n')
                    f.close()
                    self.initRole = True

            if self.toController == True and dp in self.requestDatapaths:
                self.dstMaster = True


        elif msg.role == ofp.OFPCR_ROLE_SLAVE:
            role = 'SLAVE'
            if not self.initRole:
                self.initedSWNum = self.initedSWNum + 1
                if self.initedSWNum == 16:
                    print('controller {}  initialized at {}'.format(self.controllerId, time.time()))
                    f = open('initedController', 'a+')
                    f.write(str(self.controllerId) + '\n')
                    f.close()
                    self.initRole = True

            if self.fromController == True and dp in self.requestDatapaths:
                slaveMessage = json.dumps({'srcController': self.controllerId,
                                           'dstController': self.dstController,
                                           'slave': 'True', "datapath": dpid})
                self.send(slaveMessage)
                print('del mig switch local message!!!')
                self.localDatapathsRate.pop(dp.id)
                self.dpFlowTableNum.pop(dp.id)
                self.startMigration = False  # 开始迁移的标志
                self.deleteFlag = False  # 收到删除流表的标志
                self.otherDel = False
                self.endMigration = False  # 结束迁移
                self.requestControllerID = 0  # 请求迁移的控制器
                self.requestDatapaths = []
                self.fromController = False
                self.toController = False
                self.dstController = 0
                self.respondTimelogger.info('{},src controller end migration'.format(time.time()))
        else:
            role = 'unknown'
        print('receive OFPRoleReply msg at', time.time())
        self.logger.info('OFPRoleReply received: '
                         'dpid=%s, role=%s generation_id=%d', dpid,
                         role, msg.generation_id)

    def send_barrier_request(self, datapath):
        """
        发送barrier_request消息
        """
        ofp_parser = datapath.ofproto_parser
        req = ofp_parser.OFPBarrierRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
    def barrier_reply_handler(self, ev):
        self.logger.info('OFPBarrierReply received')
        dp = ev.msg.datapath
        ofp_parse = dp.ofproto_parser
        ofp = dp.ofproto
        self.barrier_reply_Count = self.barrier_reply_Count + 1
        if self.barrier_reply_Count == 1 and self.startMigration == True and self.fromController == True:
            print('删除空流表————delete dummy flow at {} by controller {}'.format(time.time(), self.controllerId))
            match = ofp_parse.OFPMatch(in_port=1234)
            self.del_flow(dp, match)
        if self.barrier_reply_Count == 2 and self.startMigration == True and self.fromController == True:
            print('第二次barrier reply at {} at controller {}'.format(time.time(), self.controllerId))
            # time.sleep(5)
            # self.file.write('{},{}\n'.format(time.time(), '结束迁移'))
            # self.file.flush()
            # self.localDatapathsRate.pop(dp.id)
            endMigrationMsg = json.dumps({'srcController': self.controllerId,
                                          'dstController': self.dstController,
                                          'endMigration': 'True',
                                          'datapath': dp.id})
            self.send(endMigrationMsg)
            print('源控制器发送SLAVE请求')
            self.send_role_request(dp, ofp.OFPCR_ROLE_SLAVE)

    # 当控制器和交换机开始的握手动作完成后，进行table-miss(默认流表)的添加
    # 关于这一段代码的详细解析，参见：https://blog.csdn.net/weixin_40042248/article/details/115749340
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        # add table-miss
        match = ofp_parser.OFPMatch()
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(datapath=datapath, priority=0, match=match, actions=actions)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topo(self, ev):

        switch_list = get_switch(self.topology_api_app)
        print('switch_list: ', switch_list)
        # 得到每个设备的id，并写入图中作为图的节点
        for switch in switch_list:
            if switch.dp.id not in self.datapaths.keys():
                self.datapaths[switch.dp.id] = switch.dp
                print(self.datapaths)

        if self.controllerId != 5:
            return
        link_list = get_link(self.topology_api_app)
        print('link_list length is {}: '.format(len(link_list)))
        links = []
        # 将得到的链路的信息作为边写入图中
        for link in link_list:
            print('{}'.format(link))
            # print('link src: {}, dst: {}'.format(link.src,link.dst))
            links.append((link.src.dpid, link.dst.dpid, {'attr_dict': {'port': link.src.port_no}}))
        self.G.add_edges_from(links)

        for link in link_list:
            links.append((link.dst.dpid, link.src.dpid, {'attr_dict': {'port': link.dst.port_no}}))
        self.G.add_edges_from(links)

    def get_out_port(self, datapath, src, dst, in_port):
        dpid = datapath.id
        # print('get path  from {} to {}'.format( src, dst))
        # 开始时，各个主机可能在图中不存在，因为开始ryu只获取了交换机的dpid，并不知道各主机的信息，
        # 所以需要将主机存入图中
        if self.G == None:
            self.G = pickle.load(open('netGraph3', 'rb'))

        if src not in self.G:
            print('add host {} at switch {}'.format(src, dpid))
            self.G.add_node(src)
            self.G.add_edge(dpid, src, attr_dict={'port': in_port})
            self.G.add_edge(src, dpid)

        if dst in self.G and self.controllerId == 1:
            if (src, dst) not in self.paths.keys():
                self.paths = eval(open('paths3.json', 'r').read())
                # path = nx.shortest_path(self.G, src, dst)
                # print('get path:   {}'.format(path))
                # self.paths[(src, dst)] = path

            path = self.paths[(src, dst)]
            # print(self.paths)
            if len(self.paths.keys()) == 16 * 15 and not self.sendPath:
                # f = open('netGraph', 'wb')
                # pickle.dump(self.G, f)
                # f.close()
                # f = open('paths3','w')
                # f.write(self.paths.__str__())
                # f.close()
                for i in range(1, 5):
                    if self.controllerId != i:
                        message = json.dumps({'srcController': self.controllerId,
                                              'dstController': i, 'sendPath': 'True',
                                              'paths': str(self.paths)
                                              })
                        self.send(message)
                        time.sleep(1)
                self.sendPath = True

            next_hop = path[path.index(dpid) + 1]
            out_port = self.G[dpid][next_hop]['attr_dict']['port']
            # print('get path {} from {} to {} at switch {}'.format(path, src, dst, dpid))
            # print('out_port is:   {}'.format(out_port))

        elif dst in self.G and self.controllerId != 1 and self.hasPaths == True:
            if (src, dst) in self.paths:
                path = self.paths[(src, dst)]
                # print('get path {} from {} to {} at switch {}'.format(path,src,dst,dpid))
                next_hop = path[path.index(dpid) + 1]
                out_port = self.G[dpid][next_hop]['attr_dict']['port']
                # print('out_port is:   {}'.format(out_port))

        else:
            out_port = datapath.ofproto.OFPP_FLOOD
        return out_port

        # 添加流表项的方法

    def add_flow1(self, datapath, priority, match, actions, idle_timeout=5, hard_timeout=0, flags=0):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        command = ofp.OFPFC_ADD
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        req = ofp_parser.OFPFlowMod(datapath=datapath, command=command,
                                    priority=priority, match=match, instructions=inst,
                                    idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout,
                                    flags=flags)
        print('send flow mod to switch {}'.format(datapath.id))
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        self.packetInTime = time.time()
        msg = ev.msg
        datapath = msg.datapath
        ofp = datapath.ofproto
        start = time.time()
        if self.deleteFlag and self.fromController == True and datapath in self.requestDatapaths:  # 如果是源控制器，在收到删除流表信息后，忽略消packet_in消息
            if self.barrier_reply_Count == 1 and self.startMigration == True:
                print('忽略消息 from switch {} at controller {}'.format(datapath.id, self.controllerId))
                return

        if not self.deleteFlag and self.toController == True and datapath in self.requestDatapaths:  # 如果是目标控制器，在收到删除流表消息前，忽略消息Packet_IN消息
            # print(self.packetInCount)
            print('忽略消息 from switch {} at controller {}'.format(datapath.id, self.controllerId))
            return

        if self.deleteFlag and \
                self.toController == True and \
                datapath in self.requestDatapaths and \
                not self.endMigration:
            # print(self.packetInCount)
            print('暂时缓存 from switch {} at controller {}'.format(datapath.id, self.controllerId))
            self.cachePacketIn.put(ev)
            return
        time1 = time.time() - start
        start = time.time()
        ofp_parser = datapath.ofproto_parser

        dpid = datapath.id
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        time2 = time.time() - start
        start = time.time()
        if eth.ethertype == ether_types.ETH_TYPE_LLDP or eth.ethertype == ether_types.ETH_TYPE_IPV6:
            # ignore lldp packet
            # print('ignore lldp')
            return
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        # udp_pkt=pkt.get_protocol(udp.udp)
        time3 = time.time() - start
        start = time.time()
        if time.time() - start > 0.001:
            print('get udp pak spend ', time.time() - start)
        # print(pkt)

        if isinstance(arp_pkt, arp.arp):
            dst = arp_pkt.dst_ip
            src = arp_pkt.src_ip
        if isinstance(ip_pkt, ipv4.ipv4):
            dst = ip_pkt.dst
            src = ip_pkt.src
        # print('packet in at sw {} from {} to {} at {}'.format(dpid,src,dst,time.time()))
        time4 = time.time() - start
        start = time.time()
        out_port = self.get_out_port(datapath, src, dst, in_port)
        if time.time() - start > 0.001:
            print('get out port spend ', time.time() - start)
        # out_port = ofproto_v1_3.OFPP_IN_PORT
        if out_port == ofp.OFPP_FLOOD:
            # print('add host .................')
            return
        time5 = time.time() - start
        start = time.time()
        # hopDelay = TOPSIS.HOP[str(dpid)][str(self.controllerId)] / 100
        # print('hopDelay : {}'.format(hopDelay))
        # time.sleep(hopDelay)

        actions = [ofp_parser.OFPActionOutput(out_port, ofp.OFPCML_NO_BUFFER)]

        if isinstance(tcp_pkt, tcp.tcp):
            tcp_srcp = tcp_pkt.src_port
            tcp_dstp = tcp_pkt.dst_port
            # if isinstance(udp_pkt, udp.udp):
            #     udp_srcp = udp_pkt.src_port
            #     udp_dstp = udp_pkt.dst_port

            # flow = (src, dst, udp_srcp, udp_dstp).__str__()
            flow = (src, dst, tcp_srcp, tcp_dstp).__str__()
            # out_port = ofproto_v1_3.OFPP_IN_PORT
            # actions = [ofp_parser.OFPActionOutput(out_port, ofp.OFPCML_NO_BUFFER)]
            # print('tcp packet {} in at {}'.format(flow,time.time()))
            if datapath.id in self.localDatapathsRate.keys():
                if self.initRole and out_port != ofp.OFPP_FLOOD and \
                        self.dpFlowTableNum[datapath.id]['minTpPort'] != -1 and \
                        TableNum[dpid] > self.dpFlowTableNum[dpid]['num'] > 0:
                    # 流表未满，直接安装流表，并不统计
                    print('just add flow {} when flow table num is {} at switch {}'.format(flow,
                                                                                           self.dpFlowTableNum[dpid][
                                                                                               'num'], dpid))
                    self.dpFlowTableNum[dpid]['num'] += 1
                    self.selfFTPlus = True
                    # match = ofp_parser.OFPMatch(in_port=in_port, eth_type=ether_types.ETH_TYPE_IP, ip_proto=17,
                    #                             ipv4_src=src,
                    #                             ipv4_dst=dst, udp_src=udp_srcp, udp_dst=udp_dstp)
                    match = ofp_parser.OFPMatch(in_port=in_port, eth_type=ether_types.ETH_TYPE_IP, ip_proto=6,
                                                ipv4_src=src,
                                                ipv4_dst=dst, tcp_src=tcp_srcp, tcp_dst=tcp_dstp)
                    self.add_flow1(datapath=datapath, priority=1, match=match, idle_timeout=5, actions=actions, flags=0)
                    # self.localDatapathsRate[datapath.id].pop(flow)

                elif flow not in self.localDatapathsRate[datapath.id].keys():
                    # 流表满了，新到的流先进行记录，不安装流表（但是会使得控制器的负载很大）
                    flowDetail = {'lastPacketInCount': 0, 'packetInCount': 1, 'packetInRateWind': [], 'packetInRate': 0}
                    self.localDatapathsRate[datapath.id][flow] = flowDetail

                elif self.dpFlowTableNum[datapath.id]['minTpPort'] != -1 and \
                        self.localDatapathsRate[datapath.id][flow]['packetInCount'] > 6 and \
                        self.dpFlowTableNum[datapath.id]['minPacketRate'] < 4 and \
                        self.localDatapathsRate[datapath.id][flow]['packetInRate'] > self.dpFlowTableNum[datapath.id][
                    'minPacketRate'] + 5 and \
                        self.dpFlowTableNum[dpid]['num'] >= TableNum[dpid]:
                    # 交换机的流表已满，对交换机的流表进行过一次统计，并且本流的速率大于流表中最小的速率，
                    minTpPort = self.dpFlowTableNum[datapath.id]['minTpPort']
                    minPacketRate = self.dpFlowTableNum[datapath.id]['minPacketRate']
                    numDict = {"num": self.dpFlowTableNum[dpid]['num'],
                               "smallNum": 0,
                               "zeroNum": 0,  # 未使用的流表数量
                               "minInPort": -1,
                               "srcIP": 0,
                               "dstIP": 0,
                               "minTpPort": -1,
                               "minPacketRate": 100}
                    # print('switch {}, flow table message {}'.format(dp_id, numDict))
                    with open('sw{}FT.json'.format(dpid), 'w') as f:
                        f.write(numDict.__str__())
                    self.dpFlowTableNum[datapath.id]['minPacketRate'] = 100
                    self.dpFlowTableNum[datapath.id]['minTpPort'] = -1
                    start = time.time()
                    result1 = os.system(
                        'sudo ovs-ofctl --strict del-flows s{} "priority=1,tcp,in_port={},nw_src={},nw_dst={},tp_src={},tp_dst={}"'.format(
                            datapath.id,
                            self.dpFlowTableNum[datapath.id]['minInPort'],
                            self.dpFlowTableNum[datapath.id]['srcIP'],
                            self.dpFlowTableNum[datapath.id]['dstIP'],
                            minTpPort,
                            minTpPort))

                    print(
                        'del flow srcIP {} dstIP {} port {} rate {}, add flow {} rate {},spend {} at switch {}, time {}'.format(
                            self.dpFlowTableNum[datapath.id]['srcIP'],
                            self.dpFlowTableNum[datapath.id]['dstIP'],
                            minTpPort,
                            minPacketRate,
                            flow,
                            self.localDatapathsRate[datapath.id][flow]['packetInRate'],
                            time.time() - start,
                            datapath.id, time.time()))

                    # match = ofproto_v1_3_parser.OFPMatch(in_port=in_port, eth_type=ether_types.ETH_TYPE_IP, ip_proto=17,
                    #                                      ipv4_src=src,
                    #                                      ipv4_dst=dst, udp_src=udp_srcp, udp_dst=udp_dstp)
                    match = ofproto_v1_3_parser.OFPMatch(in_port=in_port, eth_type=ether_types.ETH_TYPE_IP, ip_proto=6,
                                                         ipv4_src=src,
                                                         ipv4_dst=dst, tcp_src=tcp_srcp, tcp_dst=tcp_dstp)

                    self.add_flow1(datapath=datapath, priority=1, match=match, idle_timeout=5, actions=actions, flags=0)
                    self.localDatapathsRate[datapath.id].pop(flow)

                else:
                    self.localDatapathsRate[datapath.id][flow]['packetInCount'] = \
                        self.localDatapathsRate[datapath.id][flow]['packetInCount'] + 1

        # print('{}, packet in form {} to {} at {}'.format(self.packetInTime,src,dst,dpid))

        # if out_port != ofp.OFPP_FLOOD and isinstance(arp_pkt,arp.arp):
        #     # print('add flow at switch {}'.format(datapath.id))
        #     # print('match : in_port={}, ipv4_dst={}, ipv4_src={}'.format(in_port, dst, src))
        #     match = ofp_parser.OFPMatch(in_port=in_port,eth_type=ether_types.ETH_TYPE_ARP, arp_spa=src, arp_tpa=dst)
        #     self.add_flow1(datapath=datapath, priority=1, match=match, idle_timeout=5,actions=actions,flags=0)
        time6 = time.time() - start
        start = time.time()
        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
            data = msg.data
        # 控制器指导执行的命令
        out = ofp_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=in_port, actions=actions, data=data)
        time7 = time.time() - start
        start = time.time()
        datapath.send_msg(out)
        time8 = time.time() - start
        respondTime = time.time() - self.packetInTime

        if respondTime > self.respondTime:
            # print(pkt)
            # print(len(pkt))
            # print('{},{},{},{},{},{},{},{}'.format(time1,time2,time3,time4,time5,time6,time7,time8))
            self.respondTime = respondTime
            # print('respond time is {}'.format(self.respondTime))

    def cache_packet_in_handler(self, ev):
        # self.packetInTime = time.time()
        msg = ev.msg
        datapath = msg.datapath

        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        dpid = datapath.id
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype == ether_types.ETH_TYPE_LLDP or eth.ethertype == ether_types.ETH_TYPE_IPV6:
            # ignore lldp packet
            # print('ignore lldp')
            return
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if isinstance(arp_pkt, arp.arp):
            dst = arp_pkt.dst_ip
            src = arp_pkt.src_ip
        if isinstance(ip_pkt, ipv4.ipv4):
            dst = ip_pkt.dst
            src = ip_pkt.src
        # print('packet in form {} to {} at {}'.format(src,dst,dpid))
        out_port = self.get_out_port(datapath, src, dst, in_port)
        if out_port == ofp.OFPP_FLOOD:
            # print('add host .................')
            return

        # hopDelay = TOPSIS.HOP[str(dpid)][str(self.controllerId)] / 100
        # print('hopDelay : {}'.format(hopDelay))
        # time.sleep(hopDelay)

        actions = [ofp_parser.OFPActionOutput(out_port, ofp.OFPCML_NO_BUFFER)]

        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
            data = msg.data
        # 控制器指导执行的命令
        out = ofp_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

#         ryu-manager  shortest_path_forward_ygb_2.py --observe-links --ofp-tcp-listen-port=6653
