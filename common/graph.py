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
        self.dist = None

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
def bfs(starting: str, edges: dict[str, list[edge]], callback: Callable[[str, int, str], bool]):
    visited = {}
    queue: list[tuple[int, str, str]] = [(0, starting, "")]
    visited[starting] = 0
    while len(queue) > 0:
        queue.sort()
        (dist, element, from_) = queue.pop(0)
        if visited[element] < dist:
            continue
        callback(element, dist, from_)
        for edge in edges[element]:
            if edge.n2 in visited.keys() and visited[edge.n2] <= dist + edge.length:
                continue
            
            visited[edge.n2] = dist + edge.length
            queue.append((dist + edge.length, edge.n2, element))
