import unittest
import pandas as pd
from dh_network.dh_network import DHNetwork


class TestNetworkGraph(unittest.TestCase):

    def test_initiation(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])

        network = DHNetwork(heat_sources, heat_sinks, [], [])
        self.assertIsInstance(network, DHNetwork)

    def test_fixed_radius_search(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])

        network = DHNetwork(heat_sources, heat_sinks, [], [])
        network.fixed_radius_search(100)

    def test_reduce_to_minimum_spanning_tree(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])

        network = DHNetwork(heat_sources, heat_sinks, [], [])
        network.fixed_radius_search(100)
        network.reduce_to_minimum_spanning_tree()

    def test_compute_flow(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])
        network.fixed_radius_search(100)
        network.compute_flow()

    def test_total_flow(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])
        network.fixed_radius_search(100)
        network.compute_flow()
        network.total_flow()
        network.total_flow(mode="total")

    def test_compute_transmission_line_investment(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])
        network.fixed_radius_search(100)
        network.compute_flow()
        network.compute_transmission_line_costs()
        network.compute_transmission_line_costs(mode="total")

    def test_compute_heat_exchanger_investment(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])
        network.fixed_radius_search(100)
        network.compute_flow()
        network.compute_heat_exchanger_costs()
        network.compute_heat_exchanger_costs(mode="total")

    def test_compute_pump_investment(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])
        network.fixed_radius_search(100)
        network.compute_flow()
        network.compute_pump_costs()
        network.compute_pump_costs(mode="total")

    def test_total_investment(self):
        heat_sources = pd.DataFrame({"Lon": [0, 3, 6], "Lat": [0, 0, 0],
                                     "Temperature": [100, 100, 100], "id": [1, 2, 3]})
        heat_sinks = pd.DataFrame({"Lon": [1, 5, 1], "Lat": [3, 3, 5], "Temperature": [100, 100, 100], "id": [1, 2, 3]})

        network = DHNetwork(heat_sources, heat_sinks, [[1, 2, 3]], [[4, 3, 2]])
        network.fixed_radius_search(1000000)
        network.compute_flow()
        network.generate_shape_file("./test.shp")
        print(network.number_of_transmission_lines())
        network.total_investment()
        network.total_investment(mode="total")
        print(network.remove_edge_with_highest_specific_cost(return_costs=True))

    #def test_remove_lines_above_threshold(self):

