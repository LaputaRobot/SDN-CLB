import os
import time
f=open('tableNum.txt','w')
local=1
while True:
    num=os.popen('sudo ovs-ofctl dump-flows s{} |wc -l'.format(local)).readline()
    f.write(num)
    f.flush()
    time.sleep(1)
f.close()