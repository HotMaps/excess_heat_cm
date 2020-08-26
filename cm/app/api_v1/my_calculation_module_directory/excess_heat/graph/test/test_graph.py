import unittest
from ..graph import NetworkGraph
import numpy as np


class TestNetworkGraph(unittest.TestCase):

    def test_initiation(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3], []]
        source_source_edges = [[], [2], [1], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]

        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)
        self.assertIsInstance(graph, NetworkGraph)
        self.assertEqual(graph.number_of_sources, 5)
        self.assertEqual(graph.number_of_sinks, 4)

        with self.assertRaises(ValueError):
            graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                                 [])

    def test_return_adjacency_lists(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        adj = graph.return_adjacency_lists()
        # Note that the whole network graph class is based on undirected graphs, hence it will not return bidirectional
        # defined adjacencies above, but rather return a single direction.
        self.assertSequenceEqual((source_sink_edges, source_source_edges, sink_sink_edges), adj)

    def test_add_edge_attribute(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)
        source_sink_distances = [[5], [2, 3], [2], [6], [7]]
        source_source_distances = [[], [1], [], [], []]
        sink_sink_distances = [[], [], [], []]

        try:
            graph.add_edge_attribute("distance", source_sink_distances, source_source_distances, sink_sink_distances)
        except:
            self.fail("could not set edge_attribute")

        # wrong shape of attribute
        with self.assertRaises(ValueError):
            graph.add_edge_attribute("distance", [], source_source_distances, sink_sink_distances)

    def test_get_edge_attribute(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        source_sink_distances = [[5], [2, 3], [2], [6], [7]]
        source_source_distances = [[], [1], [], [], []]
        sink_sink_distances = [[], [], [], []]
        graph.add_edge_attribute("distance", source_sink_distances, source_source_distances, sink_sink_distances)
        self.assertSequenceEqual([5, 2, 3, 2, 6, 7, 1], graph.get_edge_attribute("distance"))

    def test_reduce_to_minimum_spanning_tree(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)
        source_sink_distances = [[5], [2, 3], [2], [6], [7]]
        source_source_distances = [[], [1], [], [], []]
        sink_sink_distances = [[], [], [], []]
        graph.add_edge_attribute("distance", source_sink_distances, source_source_distances, sink_sink_distances)

        graph.reduce_to_minimum_spanning_tree("distance")
        self.assertSequenceEqual(([[0], [], [1], [2], [3]], [[], [2], [], [], []], [[], [], [], []]),
                                 graph.return_adjacency_lists())

    def test_maximum_flow(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        # sink limited
        source_capacities = [100, 100, 100, 100, 100]
        sink_capacities = [1, 4, 2, 3]
        flow = graph.maximum_flow(source_capacities, sink_capacities)
        self.assertAlmostEqual(np.sum(flow[1]), np.sum(sink_capacities), 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[0]), np.sum(flow[1]), 3)

        # source limited
        source_capacities = [5, 2, 3, 1, 1]
        sink_capacities = [100, 100, 100, 100]
        flow = graph.maximum_flow(source_capacities, sink_capacities)
        self.assertAlmostEqual(np.sum(flow[1]), np.sum(source_capacities), 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[0]), np.sum(flow[1]), 3)

    def test_edge_source_target_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        self.assertSequenceEqual([(('source', 0), ('sink', 0)), (('source', 1), ('sink', 0)), (('source', 1),
                                  ('sink', 1)), (('source', 2), ('sink', 1)), (('source', 3), ('sink', 2)),
                                  (('source', 4), ('sink', 3)), (('source', 1), ('source', 2))],
                                 graph.edge_source_target_vertices())

    def test_delete_edges(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        graph.delete_edges([(('source', 3), ('sink', 2))])
        self.assertSequenceEqual([(('source', 0), ('sink', 0)), (('source', 1), ('sink', 0)), (('source', 1),
                                  ('sink', 1)), (('source', 2), ('sink', 1)), (('source', 4), ('sink', 3)),
                                  (('source', 1), ('source', 2))],
                                 graph.edge_source_target_vertices())

    def test_number_of_edges(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        self.assertEqual(7, graph.number_of_edges())

    def test_number_of_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        self.assertEqual(9, graph.number_of_vertices())

    def test_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)

        self.assertSequenceEqual([('source', 0), ('source', 1), ('source', 2), ('source', 3), ('source', 4),
                                  ('sink', 0), ('sink', 1), ('sink', 2), ('sink', 3)],
                                 graph.vertices())

    def test_contains_vertices(self):
        source_sink_edges = [[0], [0, 1], [1], [2], [3]]
        source_source_edges = [[], [2], [], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)
        self.assertTrue(graph.contains_vertices([('source', 0)]))
        self.assertTrue(graph.contains_vertices([('source', 0), ('sink', 2)]))
        self.assertFalse(graph.contains_vertices([('source', 7), ('sink', 2)]))

    def test_decomposition(self):
        source_sink_edges = [[0], [0, 1], [1], [2], []]
        source_source_edges = [[], [2], [1], [], []]
        sink_sink_edges = [[], [], [], []]
        source_correspondence = [0, 1, 2, 3, 4]
        sink_correspondence = [0, 0, 1, 2]

        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)
        source_sink_distances = [[5], [2, 3], [2], [6], []]
        source_source_distances = [[], [1], [1], [], []]
        sink_sink_distances = [[], [], [], []]
        graph.add_edge_attribute("distance", source_sink_distances, source_source_distances, sink_sink_distances)

        components = graph.decompose_to_connected()
        self.assertEqual(2, len(components))
        self.assertEqual(3, components[0].number_of_sources)
        self.assertEqual(1, components[1].number_of_sources)
        self.assertEqual(2, components[0].number_of_sinks)
        self.assertEqual(1, components[1].number_of_sinks)

        self.assertEqual(5, components[0].number_of_edges())
        self.assertEqual(1, components[1].number_of_edges())
        self.assertEqual(5, components[0].number_of_vertices())
        self.assertEqual(2, components[1].number_of_vertices())

        self.assertSequenceEqual([(('source', 0), ('sink', 0)), (('source', 1), ('source', 2)),
                                  (('source', 1), ('sink', 0)), (('source', 1), ('sink', 1)),
                                  (('source', 2), ('sink', 1))],
                                 components[0].edge_source_target_vertices())
        self.assertSequenceEqual([(('source', 3), ('sink', 2))],
                                 components[1].edge_source_target_vertices())
        self.assertSequenceEqual([('source', 0), ('source', 1), ('source', 2), ('sink', 0), ('sink', 1)],
                                 components[0].vertices())
        self.assertSequenceEqual([('source', 3), ('sink', 2)],
                                 components[1].vertices())

        components[0].reduce_to_minimum_spanning_tree("distance")
        self.assertSequenceEqual([(('source', 0), ('sink', 0)), (('source', 1), ('source', 2)),
                                  (('source', 2), ('sink', 1))], components[0].edge_source_target_vertices())
        components[1].reduce_to_minimum_spanning_tree("distance")
        self.assertSequenceEqual([(('source', 3), ('sink', 2))], components[1].edge_source_target_vertices())


        source_capacities = [100, 100, 100]
        sink_capacities = [1, 4]
        flow = components[0].maximum_flow(source_capacities, sink_capacities)
        self.assertAlmostEqual(np.sum(flow[1]), np.sum(sink_capacities), 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[0]), np.sum(flow[1]), 3)

        # source limited
        source_capacities = [5, 2, 3]
        sink_capacities = [100, 100]
        flow = components[0].maximum_flow(source_capacities, sink_capacities)

        self.assertAlmostEqual(np.sum(flow[1]), np.sum(source_capacities), 3)
        # check continuity
        self.assertAlmostEqual(np.sum(flow[0]), np.sum(flow[1]), 3)

        self.assertTrue(components[0].contains_vertices([('source', 0)]))
        self.assertTrue(components[0].contains_vertices([('source', 0), ('sink', 1)]))
        self.assertFalse(components[0].contains_vertices([('source', 7), ('sink', 1)]))
        self.assertTrue(components[1].contains_vertices([('source', 3)]))
        self.assertTrue(components[1].contains_vertices([('source', 3), ('sink', 2)]))
        self.assertFalse(components[0].contains_vertices([('source', 7), ('sink', 2)]))

        component = components[0].decompose_to_connected()
        self.assertEqual(component[0].edge_source_target_vertices(), components[0].edge_source_target_vertices())


