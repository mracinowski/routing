from collections.abc import Callable
from queue import PriorityQueue

import logging

logger = logging.getLogger("uvicorn")


class Edge:
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
        logger.info(f"Visiting {node} from, {from_}")
        self.paths[node] = from_
        if self.target == node:
            self.dist = dist

    def compute(self):
        try:
            res = [self.target]
            while res[len(res) - 1] != self.source:
                res.append(self.paths[res[len(res) - 1]])
            res.reverse()
            return res
        except:
            return "Not path was found"


def internal_dijkstra(edges: dict[str, list[Edge]], callback: Callable[[str, int, str], bool],
                      visited: dict[str, int], queue: PriorityQueue):
    logger.info(f"Visited {visited}")
    while queue.qsize() > 0:
        (dist, element, from_) = queue.get()
        if visited[element] < dist:
            continue
        callback(element, dist, from_)
        for edge in edges[element]:
            logger.info(f"Checking {edge.n2} from, {from_}")
            if edge.n2 in visited.keys() and visited[edge.n2] <= dist + edge.length:
                continue

            visited[edge.n2] = dist + edge.length
            queue.put((dist + edge.length, edge.n2, element))


def custom_start_dijkstra(point, starting: list[tuple[str, int]], edges: dict[str, list[Edge]],
                          callback: Callable[[str, int, str], bool]):
    visited = {}
    queue: PriorityQueue[tuple[int, str, str]] = PriorityQueue()
    for i in starting:
        visited[i[0]] = i[1]
        queue.put((i[1], i[0], point))
    return internal_dijkstra(edges, callback, visited, queue)


# Does a Dijkstra algorithm, starting from starting node, and calls callback on each visited node
def dijkstra(starting: str, edges: dict[str, list[Edge]], callback: Callable[[str, int, str], bool]):
    visited = {}
    queue: PriorityQueue[tuple[int, str, str]] = PriorityQueue()
    queue.put((0, starting, ""))
    visited[starting] = 0
    return internal_dijkstra(edges, callback, visited, queue)
