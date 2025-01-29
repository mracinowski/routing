from collections.abc import Callable

class edge:
    n1: str
    n2: str
    id: str
    length: int
    
    def __init__(self, _n1, _n2, _id, _length):
        self.n1 = _n1
        self.n2 = _n2
        self.id = _id
        self.length = _length

class ResultSet1:
    
    def __init__(self):
        self.res = {}
        
    def callback(self, node: str, dist: int, _from: str):
        self.res[node] = dist
    
class PathResult:
    
    def __init__(self, source, target):
        self.paths = {}
        self.source = source
        self.target = target
        self.dist = 0
        
    def callback(self, node: str, dist: int, from_: str):
        self.paths[node] = from_
        if self.target == node:
            self.dist = dist
        
    def compute(self):
        res = []
        res.append(self.target)
        while res[len(res) - 1] != self.source:
            res.append(self.paths[res[len(res) - 1]])
        return res

# Does a bfs, starting from starting node, and calls callback on each visited node
def bfs(starting: str, edges: dict[str, list[edge]], callback: Callable[[str, int, str]]):
    visited = {}
    queue: list[tuple[str, int]] = []
    queue.append((starting, 0))
    visited[starting] = True
    while len(queue) > 0:
        (element, dist) = queue.pop(0)
        callback(element, dist)
        for edge in edges[element]:
            if visited[edge] == True:
                continue
            visited[edge] = True
            queue.append((edge.n2, dist + edge.length))    
