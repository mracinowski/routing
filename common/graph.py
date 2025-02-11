from collections.abc import Callable
from queue import PriorityQueue

import logging

logger = logging.getLogger("uvicorn")


class Edge:
    # Represents edge between n1 and n2 of a given length.
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
    # Stores distances from a given node to other nodes
    # in form of a dictionary (called res): destination->distance
    def __init__(self):
        self.res = {}

    def callback(self, node: str, dist: int, _from: str):
        """Updates node's info about its distance from source"""
        self.res[node] = dist


class PathResult:
    # Stores distance (dist) as well as path from a given node to other nodes
    # in form of a dictionary (called paths): node->previous node on path
    def __init__(self, source, target):
        self.paths = {}
        self.source = source
        self.target = target
        self.dist = None

    def callback(self, node: str, dist: int, from_: str):
        """Updates node's info about its predecessor on path"""
        logger.info(f"Visiting {node} from, {from_}")
        self.paths[node] = from_
        if self.target == node:
            self.dist = dist

    def compute(self):
        """Returns list containing a path from source to target."""
        try:
            res = [self.target]
            while res[len(res) - 1] != self.source:
                res.append(self.paths[res[len(res) - 1]])
            res.reverse()
            return res
        except:
            return "No path was found"  # nodes are not connected


def internal_dijkstra(
    edges: dict[str, list[Edge]],
    callback: Callable[[str, int, str], bool],
    visited: dict[str, int],
    queue: PriorityQueue,
):
    """Does a Dijkstra algorithm, starting from starting node, and calls callback on each visited node."""
    logger.info(f"Visited {visited}")
    while queue.qsize() > 0:
        (dist, element, from_) = queue.get()
        if visited[element] < dist:
            continue
        callback(element, dist, from_)  # Lets node (element) update its info.
        for edge in edges[element]:
            logger.info(f"Checking {edge.n2} from {from_}")
            if edge.n2 in visited.keys() and visited[edge.n2] <= dist + edge.length:
                continue

            visited[edge.n2] = dist + edge.length
            queue.put((dist + edge.length, edge.n2, element))


def dijkstra(
    starting: str,
    edges: dict[str, list[Edge]],
    callback: Callable[[str, int, str], bool],
):
    """Prepares environment to perform Dijkstra algorithm."""
    visited = {}
    queue: PriorityQueue[tuple[int, str, str]] = PriorityQueue()
    queue.put((0, starting, ""))
    visited[starting] = 0
    return internal_dijkstra(edges, callback, visited, queue)
