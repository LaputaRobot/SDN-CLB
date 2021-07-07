"""
author:Yuegb
date:2021,06,07
"""
import sys,os,time,logging
import numpy as np

if __name__=='__main__':
    respondTimelogger = logging.getLogger('respondTime')
    respondTimelogger.setLevel(level=logging.DEBUG)
    respondTimehandler = logging.FileHandler('iperf.log',
                                             encoding='UTF-8')
    respondTimelogger.addHandler(respondTimehandler)
    local=int(sys.argv[1])
    print('iperf ...............')
    firstSleep=False
    while True:
        dst=np.random.randint(1,16)
        if dst==local:
            continue
        dstAdr='10.0.0.%d'%dst
        # bw=np.random.poisson(10)
        bw=10/30
        if not firstSleep:
            time.sleep(np.random.randint(1,8))
            firstSleep=True
        T=np.random.poisson(50)

        result=os.system('iperf -u -c {} -b {}M -t {}'.format(dstAdr,bw,T))
        respondTimelogger.info('{}, iperf from 10.0.0.{} to {}, -b {}M -t {}, result : {}'.format(time.time(),local,dstAdr,bw,T,result))
        sleepTime = np.random.poisson(50)
        # print('sleep %ds'%sleepTime)
        time.sleep(sleepTime)
