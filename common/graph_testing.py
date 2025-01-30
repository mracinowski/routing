import unittest
import graph


class BFSTestCase(unittest.TestCase):
	def test_resultset(self):
		edges: dict[str, list[graph.Edge]] = {}
		edge1 = graph.Edge('v1', 'v2', 'e1', 2)
		edge1_2 = graph.Edge('v2', 'v1', 'e1', 2)
		edge2 = graph.Edge('v1', 'v3', 'e2', 4)
		edge2_2 = graph.Edge('v3', 'v1', 'e2', 4)
		edge3 = graph.Edge('v2', 'v3', 'e3', 1)
		edge3_2 = graph.Edge('v3', 'v2', 'e3', 1)
		edges['v1'] = [edge1, edge2]
		edges['v2'] = [edge1_2, edge3]
		edges['v3'] = [edge2_2, edge3_2]
		result_set = graph.ResultSet1()
		graph.bfs('v1', edges, result_set.callback)
		expected_result = {'v1': 0, 'v2': 2, 'v3': 3}
		self.assertEqual(expected_result, result_set.res)

	def test2_resultset(self):
		edges: dict[str, list[graph.Edge]] = {}
		edge1 = graph.Edge('v1', 'v2', 'e1', 2)
		edge1_2 = graph.Edge('v2', 'v1', 'e1', 2)
		edge2 = graph.Edge('v1', 'v3', 'e2', 1)
		edge2_2 = graph.Edge('v3', 'v1', 'e2', 1)
		edge3 = graph.Edge('v2', 'v3', 'e3', 1)
		edge3_2 = graph.Edge('v3', 'v2', 'e3', 1)
		edges['v1'] = [edge1, edge2]
		edges['v2'] = [edge1_2, edge3]
		edges['v3'] = [edge2_2, edge3_2]
		result_set = graph.ResultSet1()
		graph.bfs('v1', edges, result_set.callback)
		expected_result = {'v1': 0, 'v2': 2, 'v3': 1}
		self.assertEqual(expected_result, result_set.res)

	def test_pathresult(self):
		edges: dict[str, list[graph.Edge]] = {}
		edge1 = graph.Edge('v1', 'v2', 'e1', 2)
		edge1_2 = graph.Edge('v2', 'v1', 'e1', 2)
		edge2 = graph.Edge('v1', 'v3', 'e2', 4)
		edge2_2 = graph.Edge('v3', 'v1', 'e2', 4)
		edge3 = graph.Edge('v2', 'v3', 'e3', 1)
		edge3_2 = graph.Edge('v3', 'v2', 'e3', 1)
		edges['v1'] = [edge1, edge2]
		edges['v2'] = [edge1_2, edge3]
		edges['v3'] = [edge2_2, edge3_2]
		result_path = graph.PathResult('v1', 'v3')
		graph.bfs('v1', edges, result_path.callback)
		expected_result = 3
		self.assertEqual(expected_result, result_path.dist)
		expected_path = ['v3', 'v2', 'v1']
		self.assertEqual(expected_path, result_path.compute())

	def test2_resultpath(self):
		edges: dict[str, list[graph.Edge]] = {}
		edge1 = graph.Edge('v1', 'v2', 'e1', 2)
		edge1_2 = graph.Edge('v2', 'v1', 'e1', 2)
		edge2 = graph.Edge('v1', 'v3', 'e2', 1)
		edge2_2 = graph.Edge('v3', 'v1', 'e2', 1)
		edge3 = graph.Edge('v2', 'v3', 'e3', 1)
		edge3_2 = graph.Edge('v3', 'v2', 'e3', 1)
		edges['v1'] = [edge1, edge2]
		edges['v2'] = [edge1_2, edge3]
		edges['v3'] = [edge2_2, edge3_2]
		result_path = graph.PathResult('v1', 'v3')
		graph.bfs('v1', edges, result_path.callback)
		expected_result = 1
		self.assertEqual(expected_result, result_path.dist)
		expected_path = ['v3', 'v1']
		self.assertEqual(expected_path, result_path.compute())


if __name__ == '__main__':
	unittest.main()
