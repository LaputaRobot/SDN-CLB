import os,pprint
def getRAM(controllerId=1):
    myport = str(controllerId + 6652)
    result = os.popen('ps -ef|grep ryu-manager').readlines()
    otherProcRAM= {}
    for r in result:
        if '--ofp-tcp-listen-port' in r and myport not in r:
            controller = int(r.split('=')[-1][:4])-6652
            process=r.split()[1]
            otherProcRAM[str(controller)]=float(os.popen('top -bc -p{} -n1|tail -1'.format(process)).readline().split()[-3])
    return otherProcRAM
print(getRAM(2))