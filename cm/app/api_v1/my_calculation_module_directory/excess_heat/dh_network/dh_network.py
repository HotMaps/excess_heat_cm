import numpy as np
import fiona
from fiona.crs import from_epsg
from ..graph.graph_union import NetworkGraphUnion
from .dh_objects import TransmissionLine, AirLiquidHeatExchanger, LiquidLiquidHeatExchanger, LiquidPump
from ..utility import find_neighbours, transpose4with1, round_to_n
from ..parameters import *


class DHNetwork:
    def __init__(self, heat_sources, heat_sinks, heat_source_profiles, heat_sink_profiles):
        self.heat_sources = heat_sources
        self.heat_sinks = heat_sinks
        self.heat_source_profiles = heat_source_profiles
        self.heat_sink_profiles = heat_sink_profiles
        self.network = None
        self.time_unit = list(TIME_RESOLUTION_MAP.keys())[0]
        self.country = list(ELECTRICITY_PRICE_MAP.keys())[0]
        self.flows = []
        self.lifetime = 30
        self.discount_rate = 0.03
        self.operational_cost_factor = 0.01
        self.temperature = 100

    def fixed_radius_search(self, max_distance):
        source_sink_connections, source_sink_distances = find_neighbours(self.heat_sources, self.heat_sinks,
                                                                         max_distance)
        source_source_connections, source_source_distances = find_neighbours(self.heat_sources, self.heat_sources,
                                                                             max_distance)
        sink_sink_connections, sink_sink_distances = find_neighbours(self.heat_sinks, self.heat_sinks,
                                                                     max_distance)
        source_correspondence = self.heat_sources["id"].tolist()
        sink_correspondence = self.heat_sinks["id"].tolist()
        edge_attribute = ("distance", source_sink_distances, source_source_distances, sink_sink_distances)
        self.network = NetworkGraphUnion(source_sink_connections, source_source_connections, sink_sink_connections,
                                         source_correspondence, sink_correspondence, edge_attributes=[edge_attribute])

    def reduce_to_minimum_spanning_tree(self):
        self.network.reduce_to_minimum_spanning_tree("distance")
        self.network.decompose_to_connected()

    def compute_flow(self):
        flows = []
        for heat_source_capacities, heat_sink_capacities in zip(self.heat_source_profiles, self.heat_sink_profiles):
            flows.append(self.network.maximum_flow(heat_source_capacities, heat_sink_capacities))
        flows = transpose4with1(flows)
        self.flows = flows

    def heat_used(self, mode="individual"):
        total_flows = []
        for network in self.flows:
            total_flow = 0
            # slice source flow to determine total flow
            source_flow = network[0]
            for flow in source_flow:
                total_flow += (np.sum(np.abs(flow)))
            total_flows.append(total_flow)
        if mode == "total":
            total_flows = np.sum(total_flows)
        return total_flows

    def compute_transmission_line_costs(self, typ="investment", mode="individual"):
        transmission_line = TransmissionLine(time_unit=self.time_unit, country=self.country,
                                             liquid_temperature=self.temperature, lifetime=self.lifetime,
                                             discount_rate=self.discount_rate,
                                             operational_costs_factor=self.operational_cost_factor)
        cost_function = {"investment":  transmission_line.investment,
                         "annuity": transmission_line.annuity,
                         "annual_cost": transmission_line.annual_costs,
                         "operational_costs": transmission_line.operational_costs}

        costs = []
        for network, distances in zip(self.flows, self.network.get_edge_attribute("distance")):
            cost = 0
            for flow, distance in zip(network[2], distances):
                transmission_line.flow = np.abs(flow)   # ignore sign of flow direction
                transmission_line.length = 2 * distance
                transmission_line.find_recommended_selection()
                cost += cost_function[typ]()
            costs.append(cost)
        if mode == "total":
            return np.sum(costs)
        elif mode == "individual":
            return costs

    def compute_heat_exchanger_costs(self, typ="investment", mode="individual"):
        source_heat_exchanger = AirLiquidHeatExchanger(time_unit=self.time_unit, lifetime=self.lifetime,
                                                       discount_rate=self.discount_rate,
                                                       operational_costs_factor=self.operational_cost_factor)
        sink_heat_exchanger = LiquidLiquidHeatExchanger(time_unit=self.time_unit, lifetime=self.lifetime,
                                                        discount_rate=self.discount_rate,
                                                        operational_costs_factor=self.operational_cost_factor)
        cost_function_source = {"investment":  source_heat_exchanger.investment,
                                "annuity": source_heat_exchanger.annuity,
                                "annual_cost": source_heat_exchanger.annual_costs,
                                "operational_costs": source_heat_exchanger.operational_costs}
        cost_function_sink = {"investment": sink_heat_exchanger.investment,
                              "annuity": sink_heat_exchanger.annuity,
                              "annual_cost": sink_heat_exchanger.annual_costs,
                              "operational_costs": sink_heat_exchanger.operational_costs}

        costs = []
        for network in self.flows:
            heat_exchanger_costs = []
            for flow in network[0]:
                source_heat_exchanger.flow = flow
                heat_exchanger_costs.append(cost_function_source[typ]())
            for flow in network[1]:
                sink_heat_exchanger.flow = flow
                heat_exchanger_costs.append(cost_function_sink[typ]())
            costs.append(np.sum(heat_exchanger_costs))
        if mode == "total":
            return np.sum(costs)
        elif mode == "individual":
            return costs

    def compute_pump_costs(self, typ="investment", mode="individual"):
        pump = LiquidPump(time_unit=self.time_unit, lifetime=self.lifetime,
                          discount_rate=self.discount_rate,
                          operational_costs_factor=self.operational_cost_factor)

        cost_function = {"investment":  pump.investment,
                         "annuity": pump.annuity,
                         "annual_cost": pump.annual_costs,
                         "operational_costs": pump.operational_costs}

        costs = []
        for network in self.flows:
            cost = 0
            for flow in network[0]:
                pump.flow = flow
                cost += cost_function[typ]()
            costs.append(cost)
        if mode == "total":
            return np.sum(costs)
        elif mode == "individual":
            return costs

    def total_costs(self, typ="investment", mode="individual"):
        total = np.array(self.compute_transmission_line_costs(typ=typ, mode=mode)) +\
                np.array(self.compute_heat_exchanger_costs(typ=typ, mode=mode)) +\
                np.array(self.compute_pump_costs(typ=typ, mode=mode))

        if mode == "individual":
            return total.tolist()
        elif mode == "total":
            return total

    def excess_heat_available(self):
        return self.heat_sources["Excess_heat"].sum()

    def excess_heat_connected(self, mode="individual"):
        excess_heat_connected = []
        for flows, vertices in zip(self.flows, self.network.vertices()):
            excess_heat_connected.append(0)
            if len(flows[0]) > 0:
                flows = np.sum(np.abs(flows[0]), axis=1)
                vertices = list(filter(lambda x: x[0] == "source", vertices))
                for flow, vertex in zip(flows, vertices):
                    if flow > 0:
                        excess_heat_connected[-1] += self.heat_sources.iloc[vertex[1]]["Excess_heat"]

        if mode == "individual":
            return excess_heat_connected
        elif mode == "total":
            return np.sum(excess_heat_connected)

    def heat_lost(self, mode="individual"):
        transmission_line = TransmissionLine(time_unit=self.time_unit, country=self.country,
                                             liquid_temperature=self.temperature, lifetime=self.lifetime,
                                             discount_rate=self.discount_rate,
                                             operational_costs_factor=self.operational_cost_factor)
        heat_losses = []
        for network, distances in zip(self.flows, self.network.get_edge_attribute("distance")):
            heat_loss = 0
            for flow, distance in zip(network[2], distances):
                if distance == None:
                    distance = 1e15
                transmission_line.flow = np.abs(flow)   # ignore sign of flow direction
                transmission_line.length = 2 * distance
                transmission_line.find_recommended_selection()
                heat_loss += transmission_line.heat_loss()
            heat_losses.append(heat_loss)
        if mode == "total":
            return np.sum(heat_losses)
        elif mode == "individual":
            return heat_losses

    def heat_delivered(self, mode="individual"):
        return np.array(self.heat_used(mode)) - np.array(self.heat_lost(mode))

    def levelized_cost_of_heat_supply(self, mode="individual"):
        a = np.array(self.heat_delivered(mode=mode))
        if np.sum(a) > 0:
            return np.array(self.total_costs(typ="annual_cost", mode=mode)) / a
        else:
            return 0

    def pump_energy_costs(self, mode="individual"):
        transmission_line = TransmissionLine(time_unit=self.time_unit, country=self.country,
                                             liquid_temperature=self.temperature, lifetime=self.lifetime,
                                             discount_rate=self.discount_rate,
                                             operational_costs_factor=self.operational_cost_factor)
        pump_energy_costs = []
        for network, distances in zip(self.flows, self.network.get_edge_attribute("distance")):
            pump_energy_cost = 0
            for flow, distance in zip(network[2], distances):
                transmission_line.flow = np.abs(flow)  # ignore sign of flow direction
                transmission_line.length = 2 * distance
                transmission_line.find_recommended_selection()
                pump_energy_cost += transmission_line.pump_energy_cost()
            pump_energy_costs.append(pump_energy_cost)
        if mode == "total":
            return np.sum(pump_energy_costs)
        elif mode == "individual":
            return pump_energy_costs

    def remove_lines_above_threshold(self, threshold):
        transmission_line = TransmissionLine(time_unit=self.time_unit, country=self.country,
                                             liquid_temperature=self.temperature, lifetime=self.lifetime,
                                             discount_rate=self.discount_rate,
                                             operational_costs_factor=self.operational_cost_factor)
        edges_to_delete = []
        for network, distances, edges in zip(self.flows, self.network.get_edge_attribute("distance"),
                                             self.network.edge_source_target_vertices()):
            # slice connection flow of network, hence drop source and sink flows
            connection_flow = network[2]
            for flow, distance, edge in zip(connection_flow, distances, edges):
                transmission_line.flow = np.abs(flow)   # ignore sign of flow direction
                transmission_line.length = 2 * distance
                transmission_line.find_recommended_selection()
                if transmission_line.specific_costs() > threshold:
                    edges_to_delete.append(edge)

        self.network.delete_edges(edges_to_delete)

    def remove_lines_above_threshold_recursive(self, threshold):
        last_flow = -1
        self.compute_flow()
        while last_flow != self.heat_used(mode="total"):
            last_flow = self.heat_used(mode="total")
            self.remove_lines_above_threshold(threshold)
            self.compute_flow()

    def remove_edge_with_highest_specific_cost(self, mode="individual", return_costs=False):
        transmission_line = TransmissionLine(time_unit=self.time_unit, country=self.country,
                                             liquid_temperature=self.temperature, lifetime=self.lifetime,
                                             discount_rate=self.discount_rate,
                                             operational_costs_factor=self.operational_cost_factor)
        highest_specific_costs = [-1]
        edge_to_delete = None
        for network, distances, edges in zip(self.flows, self.network.get_edge_attribute("distance"),
                                             self.network.edge_source_target_vertices()):

            # slice connection flow of network, hence drop source and sink flows
            connection_flow = network[2]
            
            print("#"*25)
            print("connection_flow", connection_flow)
            print("distances", distances)
            print("edges", edges)
            
            
            
            for flow, distance, edge in zip(connection_flow, distances, edges):
                transmission_line.flow = np.abs(flow)   # ignore sign of flow direction
                transmission_line.length = 2.0 * distance
                transmission_line.find_recommended_selection()
                if transmission_line.specific_costs() > highest_specific_costs[-1]:
                    edge_to_delete = edge
                    highest_specific_costs[-1] = transmission_line.specific_costs()
            if mode == "individual":
                self.network.delete_edges([edge_to_delete])
                highest_specific_costs.append(-1)
                edge_to_delete = None

        # remove last append -1
        if mode == "individual":
            highest_specific_costs.pop()

        if mode == "total":
            self.network.delete_edges([edge_to_delete])
            return highest_specific_costs[0]

        if return_costs:
            return highest_specific_costs

    def number_of_transmission_lines(self, mode="individual"):
        if mode == "individual":
            return self.network.number_of_edges()
        elif mode == "total":
            return np.sum(self.network.number_of_edges())

    def generate_shape_file(self, file, number_of_digits=3):
        coordinates = []
        for network in self.network.edge_source_target_vertices():
            coordinates_of_network = []
            for edge in network:
                coordinates_of_line = []
                for point in edge:
                    if point[0] == "source":
                        coordinates_of_line.append((self.heat_sources.iloc[point[1]]["Lon"],
                                                    self.heat_sources.iloc[point[1]]["Lat"]))
                    else:
                        coordinates_of_line.append((self.heat_sinks.iloc[point[1]]["Lon"],
                                                    self.heat_sinks.iloc[point[1]]["Lat"]))

                coordinates_of_network.append(coordinates_of_line)
            coordinates.append(coordinates_of_network)

        output_driver = "ESRI Shapefile"
        schema = {
            "geometry": "LineString",
            "properties": dict([
                ("Flow", "str"),
                ("Temp", "str"),
                ("Length", "str")
            ])
        }

        with fiona.open(file, "w", crs=from_epsg(4326), driver=output_driver, schema=schema) as shp:
            for coordinates_of_network, lengths, flows in zip(coordinates, self.network.get_edge_attribute("distance"),
                                                              self.flows):

                if len(flows[2]) > 0:
                    flows = np.sum(np.abs(flows[2]), axis=1)
                    for coordinate, length, flow in zip(coordinates_of_network, lengths, flows):
                        line = {
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coordinate
                            },
                            "properties": dict([
                                ("Flow", str(round_to_n(flow, number_of_digits)) + " MWh/a"),
                                ("Temp", str(round_to_n(self.temperature, number_of_digits)) + " C"),
                                ("Length", str(round_to_n(length / 1000, number_of_digits)) + " km")
                            ])
                        }

                        shp.write(line)

    def heat_profile(self, target, mode="individual"):
        if target == "source":
            profiles = self.heat_source_profiles.transpose()
        else:
            profiles = self.heat_sink_profiles.transpose()
        heat_profiles = []
        for flows, vertices in zip(self.flows, self.network.vertices()):
            heat_profiles.append(np.zeros(np.shape(profiles)[1]))
            if len(flows[0]) > 0:
                flows = np.sum(np.abs(flows[0]), axis=1)
                vertices = list(filter(lambda x: x[0] == target, vertices))

                for flow, vertex in zip(flows, vertices):
                    if flow > 0:
                        heat_profiles[-1] += profiles[vertex[1]]
        if mode == "individual":
            return heat_profiles
        elif mode == "total":
            return np.sum(heat_profiles, axis=0)
