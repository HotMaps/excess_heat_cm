import unittest
import numpy as np
from ..graph_union import NetworkGraphUnion


class TestNetworkGraph(unittest.TestCase):

    def test_initiation(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3], []]
        source_source_edges = [[], [2], [1], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)

        self.assertIsInstance(graph, NetworkGraphUnion)

        with self.assertRaises(ValueError):
            graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                      [])

    def test_add_edge_attribute(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        source_sink_distances = [[5], [2, 3], [2], [6], [7]]
        source_source_distances = [[], [1], [], [], []]
        sink_sink_distances = [[], [], [], []]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence, edge_attributes=[("distance", source_sink_distances,
                                                                         source_source_distances,
                                                                         sink_sink_distances)])

        self.assertIsInstance(graph, NetworkGraphUnion)

        # wrong shape of attribute
        with self.assertRaises(ValueError):
            graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                      sink_correspondence, edge_attributes=[("distance", [],
                                                                             source_source_distances,
                                                                             sink_sink_distances)])

    def test_get_edge_attribute(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        source_sink_distances = [[5], [2, 3], [2], [6], [7]]
        source_source_distances = [[], [1], [], [], []]
        sink_sink_distances = [[], [], [], []]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence, edge_attributes=[("distance", source_sink_distances,
                                                                         source_source_distances,
                                                                         sink_sink_distances)])
        self.assertSequenceEqual([[5, 2, 3, 2, 6, 7, 1]], graph.get_edge_attribute("distance"))

    def test_reduce_to_minimum_spanning_tree(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        source_sink_distances = [[5], [2, 3], [2], [6], [7]]
        source_source_distances = [[], [1], [], [], []]
        sink_sink_distances = [[], [], [], []]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence, edge_attributes=[("distance", source_sink_distances,
                                                                         source_source_distances,
                                                                         sink_sink_distances)])

        graph.reduce_to_minimum_spanning_tree("distance")
        self.assertSequenceEqual([[(('source', 0), ('sink', 0)), (('source', 2), ('sink', 1)),
                                  (('source', 3), ('sink', 2)), (('source', 4), ('sink', 3)),
                                  (('source', 1), ('source', 2))]], graph.edge_source_target_vertices())

    def test_decompose_to_connected(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [1], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        source_sink_distances = [[5], [2, 3], [2], [6], []]
        source_source_distances = [[], [1], [1], [], []]
        sink_sink_distances = [[], [], [], []]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence, edge_attributes=[("distance", source_sink_distances,
                                                                         source_source_distances,
                                                                         sink_sink_distances)])
        graph.decompose_to_connected()
        self.assertSequenceEqual([[(('source', 0), ('sink', 0)), (('source', 1), ('source', 2)),
                                   (('source', 1), ('sink', 0)), (('source', 1), ('sink', 1)),
                                   (('source', 2), ('sink', 1))], [(('source', 3), ('sink', 2))]],
                                 graph.edge_source_target_vertices())

    def test_maximum_flow(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)

        # sink limited
        source_capacities = [100, 100, 100, 100, 100]
        sink_capacities = [1, 4, 2, 3]
        flow = graph.maximum_flow(source_capacities, sink_capacities)[0]
        self.assertAlmostEqual(np.sum(flow[1]), np.sum(sink_capacities), 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[0]), np.sum(flow[1]), 3)

        # source limited
        source_capacities = [5, 2, 3, 1, 1]
        sink_capacities = [100, 100, 100, 100]
        flow = graph.maximum_flow(source_capacities, sink_capacities)[0]
        self.assertAlmostEqual(np.sum(flow[1]), np.sum(source_capacities), 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[0]), np.sum(flow[1]), 3)

    def test_edge_source_target_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)

        self.assertSequenceEqual([[(('source', 0), ('sink', 0)), (('source', 1), ('sink', 0)),
                                  (('source', 1), ('sink', 1)), (('source', 2), ('sink', 1)),
                                  (('source', 3), ('sink', 2)), (('source', 4), ('sink', 3)),
                                  (('source', 1), ('source', 2))]], graph.edge_source_target_vertices())

    def test_delete_edges(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)

        graph.delete_edges([(('source', 3), ('sink', 2))])
        self.assertSequenceEqual([[(('source', 0), ('sink', 0)), (('source', 1), ('sink', 0)),
                                  (('source', 1), ('sink', 1)), (('source', 2), ('sink', 1)),
                                  (('source', 4), ('sink', 3)), (('source', 1), ('source', 2))]],
                                 graph.edge_source_target_vertices())

    def test_number_of_edges(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        self.assertEqual([7], graph.number_of_edges())

    def test_number_of_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)

        self.assertEqual([9], graph.number_of_vertices())

    def test_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)

        self.assertSequenceEqual([[('source', 0), ('source', 1), ('source', 2), ('source', 3), ('source', 4),
                                  ('sink', 0), ('sink', 1), ('sink', 2), ('sink', 3)]], graph.vertices())

    def test_contains_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        self.assertTrue(graph.contains_vertices([('source', 0)]))
        self.assertTrue(graph.contains_vertices([('source', 0), ('sink', 2)]))
        self.assertFalse(graph.contains_vertices([('source', 7), ('sink', 2)]))

    def test_get_edge_attribute_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [1], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        source_sink_distances = [[5], [2, 3], [2], [6], []]
        source_source_distances = [[], [1], [1], [], []]
        sink_sink_distances = [[], [], [], []]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence, edge_attributes=[("distance", source_sink_distances,
                                                                         source_source_distances,
                                                                         sink_sink_distances)])
        graph.decompose_to_connected()
        self.assertSequenceEqual([[5, 1, 2, 3, 2], [6]], graph.get_edge_attribute("distance"))

    def test_reduce_to_minimum_spanning_tree_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [1], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        source_sink_distances = [[5], [2, 3], [2], [6], []]
        source_source_distances = [[], [1], [1], [], []]
        sink_sink_distances = [[], [], [], []]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence, edge_attributes=[("distance", source_sink_distances,
                                                                         source_source_distances,
                                                                         sink_sink_distances)])
        graph.decompose_to_connected()

        graph.reduce_to_minimum_spanning_tree("distance")
        self.assertSequenceEqual([[(('source', 0), ('sink', 0)), (('source', 1), ('source', 2)),
                                  (('source', 2), ('sink', 1))], [(('source', 3), ('sink', 2))]],
                                 graph.edge_source_target_vertices())

    def test_maximum_flow_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [1], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        source_sink_distances = [[5], [2, 3], [2], [6], []]
        source_source_distances = [[], [1], [1], [], []]
        sink_sink_distances = [[], [], [], []]

        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence, edge_attributes=[("distance", source_sink_distances,
                                                                         source_source_distances,
                                                                         sink_sink_distances)])
        graph.decompose_to_connected()

        graph.reduce_to_minimum_spanning_tree("distance")
        # sink limited
        source_capacities = [100, 100, 100, 100, 100]
        sink_capacities = [1, 4, 2, 3]
        flow = graph.maximum_flow(source_capacities, sink_capacities)
        self.assertAlmostEqual(np.sum(flow[0][1]), 5, 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[0][0]), np.sum(flow[0][1]), 3)

        self.assertAlmostEqual(np.sum(flow[1][1]), 2, 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[1][0]), np.sum(flow[1][1]), 3)

        # source limited
        source_capacities = [5, 2, 3, 1, 1]
        sink_capacities = [100, 100, 100, 100]
        flow = graph.maximum_flow(source_capacities, sink_capacities)
        self.assertAlmostEqual(np.sum(flow[1][1]), 1, 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[1][0]), np.sum(flow[1][1]), 3)

    def test_edge_source_target_vertices_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        graph.decompose_to_connected()

        self.assertSequenceEqual([[(('source', 0), ('sink', 0)), (('source', 1), ('source', 2)),
                                  (('source', 1), ('sink', 0)), (('source', 1), ('sink', 1)),
                                  (('source', 2), ('sink', 1))], [(('source', 3), ('sink', 2))]],
                                 graph.edge_source_target_vertices())

    def test_delete_edges_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        graph.decompose_to_connected()

        graph.delete_edges([(('source', 3), ('sink', 2))])
        self.assertSequenceEqual([[(('source', 0), ('sink', 0)), (('source', 1), ('source', 2)),
                                   (('source', 1), ('sink', 0)), (('source', 1), ('sink', 1)),
                                   (('source', 2), ('sink', 1))], []],
                                 graph.edge_source_target_vertices())

    def test_number_of_edges_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        graph.decompose_to_connected()
        self.assertEqual([5, 1], graph.number_of_edges())

    def test_number_of_vertices_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        graph.decompose_to_connected()

        self.assertEqual([5, 2], graph.number_of_vertices())

    def test_vertices_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        graph.decompose_to_connected()

        self.assertSequenceEqual([[('source', 0), ('source', 1), ('source', 2), ('sink', 0), ('sink', 1)],
                                  [('source', 3), ('sink', 2)]], graph.vertices())

    def test_contains_vertices_split(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraphUnion(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                  sink_correspondence)
        graph.decompose_to_connected()
        self.assertTrue(graph.contains_vertices([('source', 0)]))
        self.assertTrue(graph.contains_vertices([('source', 0), ('sink', 2)]))
        self.assertFalse(graph.contains_vertices([('source', 7), ('sink', 2)]))
