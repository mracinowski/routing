import unittest
import graph


class DijkstraTestCase(unittest.TestCase):
    edges: dict[str, list[graph.Edge]] = {
        'v1': [graph.Edge('v1', 'v2', 'e1', 2),
               graph.Edge('v1', 'v3', 'e2', 4)],
        'v2': [graph.Edge('v2', 'v1', 'e1', 2),
               graph.Edge('v2', 'v3', 'e3', 1)],
        'v3': [graph.Edge('v3', 'v1', 'e2', 4),
               graph.Edge('v3', 'v2', 'e3', 1)]
    }
    edges2: dict[str, list[graph.Edge]] = {
        'v1': [graph.Edge('v1', 'v2', 'e1', 2),
               graph.Edge('v1', 'v3', 'e2', 1)],
        'v2': [graph.Edge('v2', 'v1', 'e1', 2),
               graph.Edge('v2', 'v3', 'e3', 1)],
        'v3': [graph.Edge('v3', 'v1', 'e2', 1),
               graph.Edge('v3', 'v2', 'e3', 1)]
    }

    def test_resultset(self):
        result_set = graph.ResultSet1()
        graph.dijkstra('v1', self.edges, result_set.callback)
        expected_result = {'v1': 0, 'v2': 2, 'v3': 3}
        self.assertEqual(expected_result, result_set.res)

    def test2_resultset(self):
        result_set = graph.ResultSet1()
        graph.dijkstra('v1', self.edges2, result_set.callback)
        expected_result = {'v1': 0, 'v2': 2, 'v3': 1}
        self.assertEqual(expected_result, result_set.res)

    def test_pathresult(self):
        result_path = graph.PathResult('v1', 'v3')
        graph.dijkstra('v1', self.edges, result_path.callback)
        expected_result = 3
        self.assertEqual(expected_result, result_path.dist)
        expected_path = ['v3', 'v2', 'v1']
        self.assertEqual(expected_path, result_path.compute())

    def test2_resultpath(self):
        result_path = graph.PathResult('v1', 'v3')
        graph.dijkstra('v1', self.edges2, result_path.callback)
        expected_result = 1
        self.assertEqual(expected_result, result_path.dist)
        expected_path = ['v3', 'v1']
        self.assertEqual(expected_path, result_path.compute())


if __name__ == '__main__':
    unittest.main()
