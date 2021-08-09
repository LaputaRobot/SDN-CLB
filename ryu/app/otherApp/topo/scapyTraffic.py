#! /usr/bin/env python3
import threading
from scapy.all import *
from scapy.layers.inet import IP, TCP,UDP,Ether
import sys,time,logging
import numpy as np

def sendPacket(ip_src,ip_dst,tcp_srcp,tcp_dstp,pNum,pInter):
    data = 'yuegengbiaogregaaaaaaaaaaaaaaaaaaaaaaaaaa' \
           'greagggggggggggggggggggggggggggggg' \
           'greaaaaaaaaaaaaaaaaaaaaaaaaaaaaggg' \
           'greaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'*9
    # pkt=IP(src=ip_src,dst=ip_dst)/TCP(sport=tcp_srcp,dport=tcp_dstp)/data
    pkt=IP(src=ip_src,dst=ip_dst,flags=2,id=RandShort())/UDP(sport=tcp_srcp,dport=tcp_dstp)/data
    for i in range(pNum):
        sendpfast(pkt,pps=1000, loop=10000)
        send(pkt,verbose=0)
        # print('send at {}'.format(time.time()))
        time.sleep(pInter)

def sendPacketFast(ip_src,ip_dst,tcp_srcp,tcp_dstp,loop,pps):
    data = 'yuegengbiaogregaaaaaaaaaaaaaaaaaaaaaaaaaa' \
           'greagggggggggggggggggggggggggggggg' \
           'greaaaaaaaaaaaaaaaaaaaaaaaaaaaaggg' \
           'greaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'*9
    # pkt=IP(src=ip_src,dst=ip_dst)/TCP(sport=tcp_srcp,dport=tcp_dstp)/data
    pkt=Ether()/IP(src=ip_src,dst=ip_dst,flags=2,id=RandShort())/TCP(sport=tcp_srcp,dport=tcp_dstp)/data
    sendpfast(pkt,iface='h{}-eth0'.format(ip_src.split('.')[-1]),pps=pps, loop=loop)

local=int(sys.argv[1])
# logFile='scapy.log'
# f=open(logFile,'w')
# f.close()

# scapylogger = logging.getLogger('scapyLog')
# scapylogger.setLevel(level=logging.DEBUG)
# scapyhandler = logging.FileHandler(logFile,
#                                          encoding='UTF-8')
# scapylogger.addHandler(scapyhandler)
print('scapy ...............')
# firstSleep=False
localIP='10.0.0.{}'.format(local)
newestFolder=sorted(os.listdir('../Result'))[-1]
flowCount={'big':4,'small':16}
localSeedNum=local*40
threadLock = threading.Lock()
class scapyThread(threading.Thread):
    def __init__(self,isBig,name,seedNum):
        threading.Thread.__init__(self)
        self.isBig=isBig
        self.name=name
        self.times=0
        self.firstSleep=False
        np.random.seed(seedNum)


    def run(self):
        # print('start Thread '+self.name)
        # if self.pInter==0.1:
        #     flowCount['big']=flowCount['big']-1
        # else:
        #     flowCount['small'] = flowCount['small'] - 1
        while True:
            # if not self.firstSleep:
            #     sleepT = np.random.randint(200)
            #     print('first sleep {}'.format(sleepT))
            #     time.sleep(sleepT)
            #     self.firstSleep=True
            dst = np.random.randint(1, 16)
            # dst = 2
            if dst == local:
                continue
            dstIp = '10.0.0.%d' % dst
            port = np.random.randint(100, 60000)
            # port=52918
            arrivalInter=np.random.exponential(100)
            print('arrivalInter: ',arrivalInter)
            time.sleep(arrivalInter)

            if self.isBig == 1 :
                pps = 10
                # packetNum = 300
                serveInter=np.random.exponential(100)
                loop = np.random.poisson(serveInter*pps)
                # packetNum = 700
            else:
                pps = 1
                # packetNum = 30
                serveInter = np.random.exponential(100)
                loop = np.random.poisson(serveInter * pps)
                # packetNum = 100
            startT=time.time()
            self.times+=1
            # threadLock.acquire()
            # scapylogger.info('{}-{}, {}, scapy from {} to {}, pNum: {}, pInter: {}, port: {}'.format(self.name,self.times,startT,localIP, dstIp, packetNum, pInter, port))
            # threadLock.release()
            print('{}-{}, {}, scapy from {} to {}, loop: {}, pps: {}, port: {}'.format(self.name,self.times,startT,localIP, dstIp, loop, pps, port))
            with open('../Result/'+newestFolder+'/'+'flowNum.log', 'r+') as f:
                strL=f.readlines()[-1].split(',')
                if len(strL)==5:
                    numSmall = int(strL[-3])
                    numBig = int(strL[-2])
                    numSum = int(strL[-1])
                    if self.isBig==1:
                        numBig += 1
                        numSum+=1
                    else:
                        numSmall+=1
                        numSum+=1
                    f.write('{},{},{},{},{}\n'.format(time.time(), local,str(numSmall),str(numBig),str(numSum)))
            sendPacketFast(localIP,dstIp,port,port,loop,pps)
            with open('../Result/'+newestFolder+'/'+'flowNum.log', 'r+') as f:
                strL = f.readlines()[-1].split(',')
                if len(strL) == 5:
                    numSmall = int(strL[-3])
                    numBig = int(strL[-2])
                    numSum = int(strL[-1])
                    if self.isBig == 1:
                        numBig -= 1
                        numSum -= 1
                    else:
                        numSmall -= 1
                        numSum -= 1
                    f.write('{},{},{},{},{}\n'.format(time.time(), local, str(numSmall), str(numBig), str(numSum)))
            duration=time.time()-startT
            # sleepT=np.random.poisson(100)
            print('end, {}, {}, duration: {}'.format(self.name,time.time(),duration))



# sendPacketFast('10.0.0.1','10.0.0.2',1234,1234,5000,140)
# for i in range(1,16,3):
#     scapyThread(1, 'Big-{}'.format(i), i).start()
#     scapyThread(1, 'Big-{}'.format(i+1), i+1).start()
#     scapyThread(1, 'Big-{}'.format(i+2), i+2).start()
#     time.sleep(1)
# scapyThread(0, 'small-1',11).start()
np.random.seed(localSeedNum)
big=0
small=0
bigIndex=np.random.choice(10,2)
for i in range(10):
    if i in bigIndex:
        big += 1
        threadSeed = localSeedNum + big
        scapyThread(1, 'Big-{}'.format(big), threadSeed).start()
    else:
        small += 1
        threadSeed = localSeedNum + small + 2
        scapyThread(0, 'Small-{}'.format(small), threadSeed).start()