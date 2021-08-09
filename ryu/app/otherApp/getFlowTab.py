import os
import time
local=1
while True:
    tables=os.popen('sudo ovs-ofctl dump-flows s{}'.format(local)).readlines()[1:]
    minPacketN=100
    minPort=-1
    for table in tables:
        print(table)
        details=table.split(',')
        # print(details)
        if len(details)>9:
            duration=details[1][10:-1]
            print(duration)
            n_packets=details[3][11:]
            print(n_packets)
            packetRate=int(n_packets)/float(duration)
            print(packetRate)
            srcIP=details[10][7:]
            print(srcIP)
            dstIP=details[11][7:]
            print(dstIP)
            port=details[12][7:]
            print(port)
        if n_packets<minPacketN:
            minPacketN=n_packets
            minPort=port

    time.sleep(1)