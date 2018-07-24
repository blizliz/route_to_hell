import unittest
from graph import Graph

class TestPreprocessing(unittest.TestCase):

    def test_number_edges(self):
        graph = Graph("test_map.osm")
        self.assertEqual(len(graph.edges), 3)

if __name__ == '__main__':
    unittest.main()