import collections
import json
import math
import pickle
import os
import logging
# paths={(1,2):[1,2]}
# msg=json.dumps({'paths':str(paths)})
# print(msg.__class__)
# pathGet=eval(eval(msg)['paths'])
# print(pathGet)
# print(pathGet.__class__)
# class A:
#     def __init__(self):
#         self.color='yellow'
# a=A()
# f = open('somefile', 'wb')
# pickle.dump(a, f)
# f=open('initedController','w')
# f.write('ok')
# f.close()

# mycontroller=1
# myport=str(mycontroller+6652)
# result = os.popen('ps -ef|grep ryu-manager').readlines()
# for r in result:
#     print('result:',r)
#     if myport in r:
#         process=r.split()[1]
#         print(process)
# import random
# import time
#
# logger=logging.getLogger('test_name')
# logger.setLevel(level=logging.DEBUG)
# handler=logging.FileHandler('respondTime.log',encoding='UTF-8')
# logger.addHandler(handler)
#
# for i in range(1,10):
#     time.sleep(1)
#     controllerId=1
#     r=random.Random()
#     respondTime=r.uniform(1,100)
#     start=time.time()
#     logger.info("{},{},{}".format(time.time(),respondTime,controllerId))
#     end=time.time()-start
#     print('log: ',end)
#
#     start=time.time()
#     file = open('respondTime.csv', 'w')
#     fileData={12:'feawfe',23:'faweferfr'}
#     file.seek(0)
#     file.truncate()
#     file.write(json.dumps(fileData))
#     file.flush()
#     end=time.time()-start
#     print('file: ',end)
# import TOPSIS
# import pandas as pd
# controllerId=3
# datapathId=12
# otherLoads={'1':192,'2':130,'4':200}
# otherRAM=TOPSIS.getRAM(controllerId)
# otherHop=TOPSIS.getOtherHop(str(datapathId),str(controllerId))
# dataD = {'CPU': [v for v in otherLoads.values()], 'RAM': [v for v in otherRAM.values()],
#          'hop': [v for v in otherHop.values()]}
# index = [k for k in otherHop.keys()]
# data = pd.DataFrame(dataD, index=index)
# data['CPU'] = 1 / data['CPU']
# data['RAM'] = 1 / data['RAM']
# data['hop'] = 1 / data['hop']
# dstController=int(TOPSIS.esmlb(data,TOPSIS.WEIGHT))
# print(dstController)

# otherLoads={'2': 115.98035334312063, '3': 107.6521653221125, '4': 60.83879176444309}
# myLoad=286
# avgLoad = (myLoad + sum(otherLoads.values())) / 4
# print(avgLoad)

# print(sum(abs(v-avgLoad) for v in otherLoads.values()))
# LBR=1-(abs(myLoad-avgLoad)+sum(abs(v-avgLoad) for v in otherLoads.values()))/(4*avgLoad)
# print(LBR)
# import time
# for i in range(10):
#     result=os.popen('ps -ef |grep iperf').readlines()
#     print(time.time())
#     for line in result:
#         print(line)
#     time.sleep(1)
dct={1:"2"}
print("{}".format(dct))