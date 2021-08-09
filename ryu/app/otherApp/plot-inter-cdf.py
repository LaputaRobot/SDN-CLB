import csv
import os
import sys
import matplotlib.pyplot as plt
import numpy as np

newestFolder=sorted(os.listdir('Result'))[-5]
baseFolder='Result/'+newestFolder+'/'
con1=open(baseFolder+'migInter.csv')
# con1=open('C:/Users/25247/Desktop/result-0801/nomig/respondTime1.csv')
con1CSV=csv.reader(con1,delimiter=',')

Folder2=sorted(os.listdir('Result'))[-6]
baseFolder2='Result/'+Folder2+'/'
con2=open(baseFolder2+'migInter.csv')
# con2=open('C:/Users/25247/Desktop/result-0801/esmlb/respondTime1.csv')
con2CSV=csv.reader(con2,delimiter=',')

Folder3=sorted(os.listdir('Result'))[-3]
baseFolder3='Result/'+Folder3+'/'
con3=open(baseFolder3+'migInter.csv')
# con3=open('C:/Users/25247/Desktop/result-0801/my/respondTime1.csv')
con3CSV=csv.reader(con3,delimiter=',')


con1List=list(con1CSV)
con2List=list(con2CSV)
con3List=list(con3CSV)
# for i in range(10):
#     print(con1List[i])

con1Row=len(con1List)
con2Row=len(con2List)
con3Row=len(con3List)
# print(con1Row)

con1X=[]
con1Y=[]
con2X=[]
con2Y=[]
con3X=[]
con3Y=[]
startTime1=float(con1List[1][0])
endTime=float(con1List[con1Row-1][0])
startTime2=float(con2List[1][0])
endTime2=float(con2List[con2Row-1][0])
startTime3=float(con3List[1][0])
endTime3=float(con3List[con3Row-1][0])

modle=0
for i in range(1,con1Row-1):
    if len(con1List[i])==7:
        try:
            if float(con1List[i][modle]) > 0:
                if float(con1List[i + 1][modle]) - float(con1List[i][modle]) > 40:
                    continue
                else:
                    con1X.append(float(con1List[i][0]) - startTime1)
                    con1Y.append(float(con1List[i+1][modle])-float(con1List[i][modle]))

        except ValueError as e:
            print(e)
for i in range(1,con2Row-1):
    if len(con2List[i]) == 7:
        try:
            con2X.append(float(con2List[i][0])-startTime2)
            con2Y.append(float(con2List[i+1][modle])-float(con2List[i][modle]))
        except ValueError as e:
            print(e)
for i in range(1,con3Row-1):
    if len(con3List[i]) == 7:
        try:
            con3X.append(float(con3List[i][0])-startTime3)
            con3Y.append(float(con3List[i+1][modle])-float(con3List[i][modle]))
        except ValueError as e:
            print(e)


fig = plt.figure()
# adjustFigAspect(fig,aspect=5)
ax = fig.add_subplot(111)

# 添加X/Y轴描述
ax.set_xlabel('migration interval')
if modle == 2:
    ax.set_ylabel('Controller-Load(packet/s)')
elif modle == 3:
    ax.set_ylabel('LBR')
else:
    ax.set_ylabel('CDF')
# ax.bar(con1X,con1Y,label='SMCS',linewidth=0.7)
print(sum(con1Y)/len(con1Y))
print(sum(con2Y)/len(con2Y))
ax.hist(con1Y,100,density=True,histtype='step',cumulative=True,range=(0,max(max(con1Y),max(con2Y))),label='OUR')
ax.hist(con2Y,100,density=True,histtype='step',cumulative=True,range=(0,max(max(con1Y),max(con2Y))),label='ESMLB')
# ax.hist(con3Y,100,density=True,histtype='step',cumulative=True,range=(0,50),label='3')
# ax.hist(testY,100,density=True,histtype='step',cumulative=True)
# ax.bar(con2X,con2Y,label='ESMLB',linewidth=0.7)
# ax.bar(con3X,con3Y,label='OUR',linewidth=0.7)
ax.legend(loc = 2, prop = {'size':10})
# plt.figure(figsize=(60,1))
# plt.show()
fig.savefig('/home/ygb/ESMLB/ryu/app/otherApp/Result/2021-08-06.16_15_19/inter-cdf-our-esmlb.png',dpi=300)