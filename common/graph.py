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
        
    def callback(self, node: str, dist: int):
        self[node] = dist
    
# Does a bfs, starting from starting node, and calls callback on each visited node
def bfs(starting: str, edges: dict[str, list[edge]], callback: Callable[[str, int]]):
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
