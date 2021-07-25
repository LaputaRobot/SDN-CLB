#! /usr/bin/env python3
import math
import time

TableNum = {1: 27, 2: 20, 3: 28, 4: 21, 5: 29, 6: 45, 7: 44, 8: 42, 9: 22, 10: 35, 11: 33, 12: 29, 13: 28, 14: 27,
            15: 21, 16: 10}
switchF = [42, 36, 45, 33, 40, 84, 83, 67, 32, 62, 59, 60, 56, 44, 35, 30]
print(sum(switchF) / 240 * 80 * 2)
switchFG = {}
sw = 1
for i in switchF:
    switchFG[sw] = (math.ceil(i / sum(switchF) * 538 / 5))
    sw += 1
print(switchFG)
sum = 0
with open('./topo/flowNum.log', 'r')as f:
    lines = f.readlines()
    for l in lines:
        num = int(l.split(',')[-1])
        sum += num

print(sum / len(lines))
