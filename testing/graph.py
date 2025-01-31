from uuid import uuid4
from random import randint, sample, seed
from pydantic import BaseModel

class Group(BaseModel, frozen = True):
	id: str

	def __lt__(self, other):
		return self.id < other.id

class Node(BaseModel, frozen = True):
	group: Group | None = None
	id: str

	def __lt__(self, other):
		return self.id < other.id

def new_group(id):
	return Group(id = chr(65 + id))

def new_node(group, id):
	return Node(group = group, id = str(id + 1))

def generate_spanning_tree(nodes):
	connected = []
	edges = []
	nodes = nodes.copy()

	for _ in range(len(nodes) - 1):
		connected.append(nodes.pop())
		edges.append(sorted(sample(connected, 1) + sample(nodes, 1)))

	return edges

def generate_extra_edges(nodes, edges, count, multi_edges = False):
	for _ in range(count):
		edge = sorted(sample(nodes, 2))

		if not multi_edges and edge in edges:
			continue

		edges.append(edge)

	return edges

def generate_graph(nodes, extra_edges):
	return generate_extra_edges(
		nodes,
		generate_spanning_tree(nodes),
		extra_edges
	)

def print_edges(edges):
	for (a, b) in edges:
		print(a, '--', b)

def generate_network(
	group_count,
	min_node_count,
	max_node_count,
	max_gateways_count,
	max_extra_internal_count,
	max_extra_external_count
):
	edges = dict()
	external = []
	gateways = dict()
	groups = [ new_group(i) for i in range(group_count) ]
	nodes = dict()

	for group in groups:
		node_count = randint(min_node_count, max_node_count)
		extra_count = randint(0, max_extra_internal_count)
		nodes[group] = [ new_node(group, i) for i in range(node_count) ]

		gateways[group] = sample(nodes[group],
			randint(1, min(node_count, max_gateways_count))
		)

		edges[group] = generate_graph(nodes[group], 0)

	for (a, b) in generate_graph(groups, randint(0, max_extra_external_count)):
		edge = sample(nodes[a], 1) + sample(nodes[b], 1)
		external.append(edge)

	return (groups, nodes, edges, external)

if __name__ == '__main__':
	seed(1)

	groups, nodes, edges, external = generate_network(
		group_count = 3,
		min_node_count = 5,
		max_node_count = 7,
		max_gateways_count = 2,
		max_extra_internal_count = 3,
		max_extra_external_count = 2
	)

	for group in groups:
		print("Nodes of group", group)
		for node in nodes[group]:
			print(node)
		print()

	for group in groups:
		print("Edges of group", group)
		print_edges(edges[group])
		print()

	print("External edges")
	print_edges(external)

