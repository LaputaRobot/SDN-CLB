"""
author:Yuegb
date:2021,05,10
"""
import csv
import sys

import matplotlib.pyplot as plt
import numpy as np

con1 = open('respondTime1.csv')
con1CSV = csv.reader(con1, delimiter=',')

con2 = open('respondTime2.csv')
con2CSV = csv.reader(con2, delimiter=',')
con3 = open('respondTime3.csv')
con3CSV = csv.reader(con3, delimiter=',')
con4 = open('respondTime4.csv')
con4CSV = csv.reader(con4, delimiter=',')

con1List = list(con1CSV)
con2List = list(con2CSV)
con3List = list(con3CSV)
con4List = list(con4CSV)
# for i in range(10):
#     print(con1List[i])

con1Row = len(con1List)
con2Row = len(con2List)
con3Row = len(con3List)
con4Row = len(con4List)
# print(con1Row)

con1X = []
con1Y = []
con2X = []
con2Y = []
con3X = []
con3Y = []
con4X = []
con4Y = []

for i in range(1, con1Row):
    if len(con1List[i]) == 8:
        try:
            con1X.append(i)
            con1Y.append([int(con1List[i][1]),
                          int(con1List[i][3]),
                          int(con1List[i][5]),
                          int(con1List[i][7])])
        except ValueError as e:
            print(e)
for i in range(1, con2Row):
    if len(con2List[i]) == 8:
        try:
            con2X.append(i)
            con2Y.append([int(con2List[i][1]),
                          int(con2List[i][3]),
                          int(con2List[i][5]),
                          int(con2List[i][7])])
        except ValueError as e:
            print(e)
for i in range(1, con3Row):
    if len(con3List[i]) == 8:
        try:
            con3X.append(i)
            con3Y.append([int(con3List[i][1]),
                          int(con3List[i][3]),
                          int(con3List[i][5]),
                          int(con3List[i][7])])
        except ValueError as e:
            print(e)
for i in range(1, con4Row):
    if len(con4List[i]) == 8:
        try:
            con4X.append(i)
            con4Y.append([int(con4List[i][1]),
                          int(con4List[i][3]),
                          int(con4List[i][5]),
                          int(con4List[i][7])])
        except ValueError as e:
            print(e)


# 1052开始迁移
# 1057结束迁移
# for i in range(0,10):
#     print(con1X[i])
#     print(con1Y[i])

# print(len(con1X))
# print(len(con1Y))
# conLoadSum=[]
# conLoadSumX=[]
#
# print(sum(con1Y[10:90])/len(con1Y[10:90]))
# print(sum(con2Y[10:90])/len(con2Y[10:90]))
# print(sum(con3Y[10:90])/len(con3Y[10:90]))
# print(sum(con4Y[10:90])/len(con4Y[10:90]))

def adjustFigAspect(fig, aspect=1):
    '''
    Adjust the subplot parameters so that the figure has the correct
    aspect ratio.
    '''
    xsize, ysize = fig.get_size_inches()
    minsize = min(xsize, ysize)
    xlim = .4 * minsize / xsize
    ylim = .4 * minsize / ysize
    if aspect < 1:
        xlim *= aspect
    else:
        ylim /= aspect
    fig.subplots_adjust(left=.5 - xlim,
                        right=.5 + xlim,
                        bottom=.5 - ylim,
                        top=.5 + ylim)


fig = plt.figure()
# adjustFigAspect(fig,aspect=2)
ax = fig.add_subplot(111)

# 添加X/Y轴描述
ax.set_xlabel('f t n')

ax.set_ylabel('times')

end = con1X[-1]
# plt.annotate('Start Migration', xy=(1052, 3767/3500), xytext=(1070, 3767/3500),arrowprops=dict(facecolor='black', shrink=0.05))
# plt.annotate('End Migration', xy=(1057, 0.5), xytext=(1057, 0.75),arrowprops=dict(facecolor='black', shrink=0.05))
# lable="controller{}-SMCS"
lable = "switch{}-num"
TableNum = {}
xNum = [i for i in range(1, 1001)]
for i in range(1, 17):
    if 1 <= i <= 4:
        TableNum[i] = int(sum([int(con1List[r][2 * i - 1]) for r in xNum]) / 5000)
    if 5 <= i <= 8:
        TableNum[i] = int(sum([int(con2List[r][(i - 4) * 2 - 1]) for r in xNum]) / 5000)
    if 9 <= i <= 12:
        TableNum[i] = int(sum([int(con3List[r][(i - 8) * 2 - 1]) for r in xNum]) / 5000)
    if 13 <= i <= 16:
        TableNum[i] = int(sum([int(con4List[r][(i - 12) * 2 - 1]) for r in xNum]) / 5000)

print(TableNum)
sys.exit(0)

ax.plot(con1X, [int(con1List[i][1]) for i in con1X], label=lable.format(1), linewidth=0.7)
ax.plot(con1X, [int(con1List[i][3]) for i in con1X], label=lable.format(2), linewidth=0.7)
ax.plot(con1X, [int(con1List[i][5]) for i in con1X], label=lable.format(3), linewidth=0.7)
ax.plot(con1X, [int(con1List[i][7]) for i in con1X], label=lable.format(4), linewidth=0.7)
ax.plot(con2X, [int(con2List[i][1]) for i in con2X], label=lable.format(5), linewidth=0.7)
ax.plot(con2X, [int(con2List[i][3]) for i in con2X], label=lable.format(6), linewidth=0.7)
ax.plot(con2X, [int(con2List[i][5]) for i in con2X], label=lable.format(7), linewidth=0.7)
ax.plot(con2X, [int(con2List[i][7]) for i in con2X], label=lable.format(8), linewidth=0.7)
ax.plot(con3X, [int(con3List[i][1]) for i in con3X], label=lable.format(9), linewidth=0.7)
ax.plot(con3X, [int(con3List[i][3]) for i in con3X], label=lable.format(10), linewidth=0.7)
ax.plot(con3X, [int(con3List[i][5]) for i in con3X], label=lable.format(11), linewidth=0.7)
ax.plot(con3X, [int(con3List[i][7]) for i in con3X], label=lable.format(12), linewidth=0.7)
ax.plot(con4X, [int(con4List[i][1]) for i in con4X], label=lable.format(13), linewidth=0.7)
ax.plot(con4X, [int(con4List[i][3]) for i in con4X], label=lable.format(14), linewidth=0.7)
ax.plot(con4X, [int(con4List[i][5]) for i in con4X], label=lable.format(15), linewidth=0.7)
ax.plot(con4X, [int(con4List[i][7]) for i in con4X], label=lable.format(16), linewidth=0.7)
# ax.plot(con1X,con1Y[1],label=lable.format(2),linewidth=0.7)
# ax.plot(con1X,con1Y[2],label=lable.format(3),linewidth=0.7)
# ax.plot(con1X,con1Y[3],label=lable.format(4),linewidth=0.7)
# ax.plot(con2X,con2Y[0],label=lable.format(5),linewidth=0.7)
# ax.plot(con2X,con2Y[1],label=lable.format(6),linewidth=0.7)
# ax.plot(con2X,con2Y[2],label=lable.format(7),linewidth=0.7)
# ax.plot(con2X,con2Y[3],label=lable.format(8),linewidth=0.7)
# ax.plot(con3X,con3Y[0],label=lable.format(9),linewidth=0.7)
# ax.plot(con3X,con3Y[1],label=lable.format(10),linewidth=0.7)
# ax.plot(con3X,con3Y[2],label=lable.format(11),linewidth=0.7)
# ax.plot(con3X,con3Y[3],label=lable.format(12),linewidth=0.7)
# ax.plot(con4X,con4Y[0],label=lable.format(13),linewidth=0.7)
# ax.plot(con4X,con4Y[1],label=lable.format(14),linewidth=0.7)
# ax.plot(con4X,con4Y[2],label=lable.format(15),linewidth=0.7)
# ax.plot(con4X,con4Y[3],label=lable.format(16),linewidth=0.7)
# ax.axhline(y=130, color='r', linestyle='-')
# ax.plot(conLoadSumX,conLoadSum,label='controller-Sum-ESMLB',linewidth=0.7)
# ax.set_xlim(endTime-startTime-100,endTime-startTime)
ax.set_xlim(0, end)
# ax.set_xlim(150,200)
# ax.set_ylim(0,450)
# ax = plt.gca()
# start, end = ax.get_xlim()
# # 设置x轴刻度的显示步长

ax.legend(loc=1, prop={'size': 5})
# plt.figure(figsize=(60,1))
plt.show()
# fig.savefig('load-smcs.png', dpi=300)
