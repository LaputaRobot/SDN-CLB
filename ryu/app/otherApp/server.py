#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import contextlib
import json
import os
import threading
import time
import traceback

from ryu.lib import hub
from ryu.lib.hub import StreamServer

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

ResultFolder= 'Result/'+time.strftime('%Y-%m-%d.%H_%M_%S')
if not os.path.exists(ResultFolder):
	os.makedirs(ResultFolder)

f = open(ResultFolder+'/migInter.csv', 'w')
f.close()
f = open(ResultFolder+'/flowNum.log', 'w')
f.write('{},{},{},{},{}\n'.format(time.time(), 0, 0,0,0))
f.close()
f = open('initedController', 'w')
f.close()
# f = open("/home/ygb/ESMLB/ryu/app/otherApp/topo/iperf.log", 'w')
# f.close()
f = open('lock', 'w')
f.write('False')
f.close()

for i in range(1, 5):
	f = open(ResultFolder+'/respondTime{}.csv'.format(i), 'w')
	f.close()

TableNum = {1: 6, 2: 5, 3: 6, 4: 5, 5: 6, 6: 12, 7: 12, 8: 9, 9: 5, 10: 9, 11: 8, 12: 8, 13: 8, 14: 6, 15: 5, 16: 4}
for k in TableNum:
    TableNum[k] =  7+2

class Server(object):
	def __init__(self, *args):
		super(Server, self).__init__()
		self.clients = {} #client = controller
		self.server = StreamServer(('0.0.0.0', 8888), self._connect)
		self.topo = {}
		

	def _connect(self, socket, address):
		print('connected address:%s' % str(address))
		
		with contextlib.closing(Client(socket)) as client:
			client.server = self  
			client_id = len(self.clients)+1 

			client.set_id(client_id)
			self.clients[client_id] = client
			client.start()

	def start(self):
		# hub.spawn(self.monitor)
		print("Server start...")
		self.server.serve_forever()
		
	def monitor(self):
		while True:
			print(self.topo)
			hub.sleep(2)

class Client(object):
	def __init__(self, socket):
		super(Client, self).__init__()
		self.send_queue = hub.Queue(32) #controller and server send message
		self.status = True
		self.server = None  # connect to server
		self.socket = socket
		self.client_id = 0
		self.startGetFT=False

	def set_id(self,client_id):
		self.client_id = client_id
		msg = json.dumps({
			'cmd': 'set_id',
			'client_id': client_id,
			'resultFolder':ResultFolder
		})
		self.send(msg)

	def send(self,msg):
		if self.send_queue:
			self.send_queue.put(msg)

	def send_msg(self):
		try:
			while self.status:
				message = self.send_queue.get()
				message += '\n'
				self.socket.sendall(bytes(message,'utf-8'))
				print(message)
				hub.sleep(0.1)
		finally:# disconnect
			self.send_queue = None

	def rece_msg(self):
		while self.status:
			try:
				message = self.socket.recv(128)
				# print('try get message: ',message)
				message = message.decode('utf-8')
				if len(message) == 0:
					log.info("connection fail")
					self.status = False
					break
				while '\n' != message[-1]:
					message += self.socket.recv(128).decode('utf-8')
				# print('message now is {}'.format(message))
				msg = message.split('\n')
				print('msg len is ',len(msg))
				if self.client_id==1 and self.startGetFT==False:
					getFTThread(1).start()
					getFTThread(2).start()
					self.startGetFT=True
				for m in msg:
					if m != '':
						messageDict = eval(m)
						dstController = messageDict['dstController']
						print('send msg {} to {}'.format(m, dstController))
						m+='\n'
						self.server.clients[dstController].socket.sendall(m.encode('utf-8'))
				hub.sleep(0.1)
			except ValueError:
				print(('Value error for %s, len: %d', message, len(message)))



	def start(self):
		# print('client start()...')
		t1 = hub.spawn(self.send_msg)
		t2 = hub.spawn(self.rece_msg)
		hub.joinall([t1, t2])

	def close(self):
		self.status = False
		self.socket.close()

def main():
	Server().start()


class getFTThread(threading.Thread):
	def __init__(self,name):
		threading.Thread.__init__(self)
		self.dpFlowTableNum = {}
		self.name=name
		if self.name=='1':
			for i in range(1, 9):
				self.dpFlowTableNum[i] = i
		else:
			for i in range(9, 17):
				self.dpFlowTableNum[i] = i

	def run(self):
		while True:
			try:
				# start=time.time()
				for dp_id in self.dpFlowTableNum.keys():
					# print('get switch {} flow table number!!!'.format(dp_id))
					tables = os.popen('sudo ovs-ofctl dump-flows s{}'.format(dp_id)).readlines()[1:]
					# print('time1', time.time() - start)
					minPacketRate = 100
					minTpPort = 0
					minInPort = "0"
					minSrcIp = "0"
					minDstIp = "0"
					smallNum = 0  # 老鼠流表的数量
					for table in tables:
						# print(table)
						details = table.split(',')
						# print(details)
						if len(details) > 9:
							duration = details[1][10:-1]
							n_packets = details[3][11:]
							if float(duration) < 1:
								# 只算稳定的流表
								continue
							packetRate = int(n_packets) / float(duration)
							in_port = details[9][-1]
							srcIP = details[10][7:]
							dstIP = details[11][7:]
							tp_port = details[12][7:]
							# print('switch {}, in_port:{}, srcIP:{}, dstIP:{}, Rate:{}, duration:{}, tp_port:{}'.format(dp_id,in_port,srcIP,dstIP,packetRate,duration,tp_port))
							if packetRate < 2:
								smallNum += 1
							if 0 < packetRate < minPacketRate:
								minPacketRate = packetRate
								minInPort = in_port
								minSrcIp = srcIP
								minDstIp = dstIP
								minTpPort = tp_port
					numDict = {"num": len(tables),
							   "smallNum": smallNum,
							   "zeroNum": TableNum[dp_id] - len(tables),  # 未使用的流表数量
							   "minInPort": minInPort,
							   "srcIP": minSrcIp,
							   "dstIP": minDstIp,
							   "minTpPort": minTpPort,
							   "minPacketRate": minPacketRate}
					# print('switch {}, flow table message {}'.format(dp_id, numDict))
					with open('sw{}FT.json'.format(dp_id), 'w') as f:
						f.write(numDict.__str__())
					# print('get switch {} flow table num spend {} at {}'.format(dp_id, time.time() - start,time.time()))
					# start = time.time()
				time.sleep(0.1)
			except Exception as e:
				traceback.print_exc()
				print(e)

if __name__ == '__main__':
	main()
