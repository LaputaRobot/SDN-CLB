class TcpPacket:
    def __init__(self, srcIp, dstIp, port, dataLen):
        self.srcIp = srcIp
        self.dstIp = dstIp
        self.port = port
        self.dataLen = dataLen


class FlowPacket:
    def __init__(self, tcpPacket):
        self.tcpPacket = tcpPacket
        self.inPort = 0
        self.type = None
        self.action = None
        self.next = None


def auto_str(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    cls.__str__ = __str__
    return cls


@auto_str
class Flow:
    def __init__(self, start_time, src, dst, port, rate, len_of_time):
        self.start_time = start_time
        self.src = src
        self.dst = dst
        self.port = port
        self.rate = rate
        self.len_of_time = len_of_time
