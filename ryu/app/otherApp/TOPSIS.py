"""
author:Yuegb
date:2021,06,06
"""
import sys
import time

import pandas as pd
import numpy as np
import os
np.set_printoptions(suppress=True)

HOP = {'1': {'1': 1, '2': 2, '3': 3, '4': 4}, '2': {'1': 1, '2': 2, '3': 3, '4': 4},
       '3': {'1': 1, '2': 2, '3': 3, '4': 4}, '4': {'1': 1, '2': 2, '3': 3, '4': 4},
       '5': {'1': 2, '2': 1, '3': 2, '4': 3}, '6': {'1': 2, '2': 1, '3': 2, '4': 3},
       '7': {'1': 2, '2': 1, '3': 2, '4': 3}, '8': {'1': 2, '2': 1, '3': 2, '4': 3},
       '9': {'1': 3, '2': 2, '3': 1, '4': 2}, '10': {'1': 3, '2': 2, '3': 1, '4': 2},
       '11': {'1': 3, '2': 2, '3': 1, '4': 2}, '12': {'1': 3, '2': 2, '3': 1, '4': 2},
       '13': {'1': 4, '2': 3, '3': 2, '4': 1}, '14': {'1': 4, '2': 3, '3': 2, '4': 1},
       '15': {'1': 4, '2': 3, '3': 2, '4': 1}, '16': {'1': 4, '2': 3, '3': 2, '4': 1}}
WEIGHT = [0.7, 0.2, 0.1]

def getOtherHop(dpId,myControllerId):
    otherHop={}
    for con in range(1,5):
        if str(con)!=myControllerId:
            otherHop[str(con)]=HOP[dpId][str(con)]
    return otherHop


def getRAM(controllerId=1):
    try:
        myport = str(controllerId + 6652)
        result = os.popen('ps -ef|grep ryu-manager').readlines()
        otherProcRAM = {}
        for r in result:
            if '--ofp-tcp-listen-port' in r and myport not in r:
                controller = int(r.split('=')[-1][:4]) - 6652
                process = r.split()[1]
                # print('process',process)
                numStr = os.popen('top -bc -p{} -n1|tail -1'.format(process)).readline().split()[9]
                # print("****************************8888888"+numStr)
                otherProcRAM[str(controller)] = float(numStr)
        return otherProcRAM
    except Exception as e:
        print(e)



def topsis(data, weight=None):
    # 归一化
    # data = data / (data).sum()
    data = data / np.sqrt((data ** 2).sum())
    print('归一化：',data)

    # 最优最劣方案
    Z = pd.DataFrame([data.min(), data.max()], index=['负理想解', '正理想解'])

    # 距离
    weight = entropyWeight(data) if weight is None else np.array(weight)
    Result = data.copy()
    Result['正理想解'] = np.sqrt(((data - Z.loc['正理想解']) ** 2 * weight).sum(axis=1))
    Result['负理想解'] = np.sqrt(((data - Z.loc['负理想解']) ** 2 * weight).sum(axis=1))

    # 综合得分指数
    Result['综合得分指数'] = Result['负理想解'] / (Result['负理想解'] + Result['正理想解'])
    Result['排序'] = Result.rank(ascending=False)['综合得分指数']

    return Result


def entropyWeight(data):
    data = np.array(data)
    # 归一化
    P = data / data.sum(axis=0)

    # 计算熵值
    E = np.nansum(-P * np.log(P) / np.log(len(data)), axis=0)

    # 计算权系数
    return (1 - E) / (1 - E).sum()

def esmlb(data, weight=None):
    # 归一化
    data = data / (data).sum()
    # data = data / np.sqrt((data ** 2).sum())
    # print('归一化：',data)
    if weight is not None:
        data=data.dot(np.diag(weight))
    # print('加权矩阵：',data)
    Z = pd.DataFrame([data.min(), data.max()], index=['负理想解', '正理想解'])
    Result = data.copy()
    Result['正理想解'] = np.sqrt(((data - Z.loc['正理想解']) ** 2 ).sum(axis=1))
    Result['负理想解'] = np.sqrt(((data - Z.loc['负理想解']) ** 2 ).sum(axis=1))
    Result['综合得分指数'] = Result['负理想解'] / (Result['负理想解'] + Result['正理想解'])
    Result['排序'] = Result.rank(ascending=False)['综合得分指数']
    print(Result)
    return Result['排序'].idxmin()

# print(getRAM(1))
#

def main():
    controllerId=2
    start=time.time()
    otherLoad={'1':192,'3':130,'4':200}
    otherRAM={'1':1,'3':1,'4':1}
    otherHop=getOtherHop(str(controllerId),'1')
    print('spend time1: ',time.time()-start)

    dataD={'CPU':[v for v in otherLoad.values()],'RAM':[v for v in otherRAM.values()],'hop':[v for v in otherHop.values()]}
    index=[k for k in otherHop.keys()]
    print('dictD: ',dataD)
    print('index: ',index)

    data=pd.DataFrame(dataD,index=index)
    data['CPU']=1/data['CPU']
    data['RAM']=1/data['RAM']
    data['hop']=1/data['hop']
    print(data)

    weight=[0.25,0.25,0.25]
    result = esmlb(data,weight)
    # result1 = topsis(data,weight)

    # print('result',result)
    # print('result1',result1)

    print(result.__class__)
    # print(result1['排序'].idxmin())
    print('spend time: ',time.time()-start)

if __name__=='__main__':
    main()