"""
author:Yuegb
date:2021,05,10
"""
import csv
import os
import sys

import matplotlib.pyplot as plt
import numpy as np


newestFolder=sorted(os.listdir('Result'))[-1]
baseFolder='Result/'+newestFolder+'/'
con1=open(baseFolder+'respondTime1.csv')
# con1=open('C:/Users/25247/Desktop/result-0801/nomig/respondTime1.csv')
con1CSV=csv.reader(con1,delimiter=',')

con2=open(baseFolder+'respondTime2.csv')
# con2=open('C:/Users/25247/Desktop/result-0801/esmlb/respondTime1.csv')
con2CSV=csv.reader(con2,delimiter=',')
con3=open(baseFolder+'respondTime3.csv')
# con3=open('C:/Users/25247/Desktop/result-0801/my/respondTime1.csv')
con3CSV=csv.reader(con3,delimiter=',')
con4=open(baseFolder+'respondTime4.csv')
# con4=open('C:/Users/25247/Desktop/result-0801/esmlb/respondTime1.csv')
con4CSV=csv.reader(con4,delimiter=',')

con1List=list(con1CSV)
con2List=list(con2CSV)
con3List=list(con3CSV)
con4List=list(con4CSV)
# for i in range(10):
#     print(con1List[i])

con1Row=len(con1List)
con2Row=len(con2List)
con3Row=len(con3List)
con4Row=len(con4List)
# print(con1Row)

con1X=[]
con1Y=[]
con2X=[]
con2Y=[]
con3X=[]
con3Y=[]
con4X=[]
con4Y=[]
startTime1=float(con1List[1][0])
endTime1=float(con1List[con1Row-1][0])
startTime2=float(con2List[1][0])
endTime2=float(con2List[con2Row-1][0])
startTime3=float(con3List[1][0])
endTime3=float(con3List[con3Row-1][0])
modle=4
offset=0
for i in range(1,con1Row):
    if len(con1List[i])==10:
        try:

            if float(con1List[i][modle]) > 0:
                con1X.append(float(con1List[i][0]) - startTime1 - offset)
                con1Y.append(float(con1List[i][modle]))
        except ValueError as e:
            print(e)
con2XX=[]
index=0
for i in range(1,con2Row):
    if len(con2List[i]) == 10:
        try:
            con2X.append(float(con2List[i][0])-startTime2-offset)
            con2Y.append(float(con2List[i][modle]))
            con2XX.append(index)
            index+=1
        except ValueError as e:
            print(e)
for i in range(1,con3Row):
    if len(con3List[i]) == 10:
        try:
            con3X.append(float(con3List[i][0])-startTime3)
            con3Y.append(float(con3List[i][modle]))
        except ValueError as e:
            print(e)
for i in range(1,con4Row):
    if len(con4List[i]) == 10:
        try:
            con4X.append(float(con4List[i][0])-startTime2)
            con4Y.append(float(con4List[i][modle]))
        except ValueError as e:
            print(e)
#1052开始迁移
#1057结束迁移
# for i in range(0,10):
#     print(con1X[i])
#     print(con1Y[i])

print(sum(con1Y[20:-20])/len(con1Y[20:-20]))
print(sum(con2Y[20:-20])/len(con2Y[20:-20]))
print(sum(con3Y[20:-20])/len(con3Y[20:-20]))
# print(sum(con4Y[10:90])/len(con4Y[10:90]))

def adjustFigAspect(fig,aspect=1):
    '''
    Adjust the subplot parameters so that the figure has the correct
    aspect ratio.
    '''
    xsize,ysize = fig.get_size_inches()
    minsize = min(xsize,ysize)
    xlim = .4*minsize/xsize
    ylim = .4*minsize/ysize
    if aspect < 1:
        xlim *= aspect
    else:
        ylim /= aspect
    fig.subplots_adjust(left=.5-xlim,
                        right=.5+xlim,
                        bottom=.5-ylim,
                        top=.5+ylim)

fig = plt.figure()
# adjustFigAspect(fig,aspect=5)
ax = fig.add_subplot(111)

# 添加X/Y轴描述
ax.set_xlabel('time(s)')
if modle == 2:
    ax.set_ylabel('Controller-Load(packet/s)')
elif modle == 3:
    ax.set_ylabel('LBR')

CDFX = np.linspace(min(con1Y), max(con1Y), len(con1Y))
CDFY = np.array(con1Y)
count, bins_count = np.histogram(CDFY, bins=10)
pdf = count / sum(count)
cdf = np.cumsum(pdf)
# plt.plot(bins_count[1:], cdf)

# ax.plot(CDFX,CDFY)
# plt.show()
# CDFY=CDFY/np.sum(con1Y)
# plt(CDFX,CDFY)
# plt.annotate('Start Migration', xy=(1052, 3767/3500), xytext=(1070, 3767/3500),arrowprops=dict(facecolor='black', shrink=0.05))
# plt.annotate('End Migration', xy=(1057, 0.5), xytext=(1057, 0.75),arrowprops=dict(facecolor='black', shrink=0.05))
# ax.plot(con1X,con1Y,label='SMCS',linewidth=0.7)
# ax.plot(con2X,con2Y,label='ESMLB',linewidth=0.7)
ax.plot(con3X,con3Y,label='OUR',linewidth=0.7)
# ax.plot(con4X,con4Y,label='controller4-SMCS',linewidth=0.7)
# ax.plot(conLoadSumX,conLoadSum,label='controller-Sum-ESMLB',linewidth=0.7)
# ax.set_xlim(endTime-startTime-200,endTime-startTime)
ax.set_xlim(0,endTime1-startTime1)
# ax.set_xlim(0,500)
ax.set_ylim(0.4,1)
# ax = plt.gca()
# start, end = ax.get_xlim()
# # 设置x轴刻度的显示步长

ax.legend(loc = 1, prop = {'size':5})
# plt.figure(figsize=(60,1))
plt.show()
# fig.savefig('C:/Users/25247/Desktop/result-0801/nomig/lbr.png', dpi=300)