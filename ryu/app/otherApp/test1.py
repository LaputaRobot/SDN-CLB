import pickle
import networkx as nx
class A:
    def __init__(self):
        self.year=1
        self.G = nx.DiGraph()
a=A()

f = open('netGraph', 'rb')
a.G = pickle.load(f)
print(a.G[1])