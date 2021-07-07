"""
author:Yuegb
date:2021,06,07
"""
import sys,os,time
import numpy as np
if __name__=='__main__':
    local=sys.argv[1]
    print('iperf ...............')
    while True:
        dst=np.random.randint(1,9)
        if dst==local:
            continue
        dstAdr='10.0.0.%d'%dst
        bw=np.random.poisson(10)
        bw=float(bw)/50
        T=np.random.poisson(10)
        os.system('iperf -u -c {} -b {}M -t {}'.format(dstAdr,bw,T))
        sleepTime = np.random.poisson(5)
        # print('sleep %ds'%sleepTime)
        time.sleep(sleepTime)
