from .graph import NetworkGraph


class NetworkGraphUnion:
    def __init__(self, source_sink_edges, source_source_edges, sink_sink_edges,
                 source_correspondence, sink_correspondence, edge_attributes=()):
        graph = NetworkGraph(source_sink_edges, source_source_edges, sink_sink_edges, source_correspondence,
                             sink_correspondence)
        self.graphs = [graph]
        for edge_attribute in edge_attributes:
            self.__add_edge_attribute(*edge_attribute)

    def __add_edge_attribute(self, name, source_sink_attributes, source_source_attributes, sink_sink_attributes):
        if len(self.graphs) > 1:
            raise ValueError("edge attribute can not be added if graph is decomposed")
        else:
            self.graphs[0].add_edge_attribute(name, source_sink_attributes, source_source_attributes,
                                              sink_sink_attributes)

    def get_edge_attribute(self, name):
        attributes = []
        for graph in self.graphs:
            attributes.append(graph.get_edge_attribute(name))
        return attributes

    def reduce_to_minimum_spanning_tree(self, name):
        for graph in self.graphs:
            graph.reduce_to_minimum_spanning_tree(name)

    def decompose_to_connected(self):
        new_graphs = []
        for graph in self.graphs:
            new_graphs.append(graph.decompose_to_connected())
        self.graphs = [item for sublist in new_graphs for item in sublist]  # flatten output

    def maximum_flow(self, source_capacities, sink_capacities):
        maximum_flows = []
        for graph in self.graphs:
            vertices = graph.vertices()
            sources = []
            sinks = []
            for vertex in vertices:
                if vertex[0] == "source":
                    sources.append(source_capacities[vertex[1]])
                else:
                    sinks.append(sink_capacities[vertex[1]])
            maximum_flows.append(graph.maximum_flow(sources, sinks))

        return maximum_flows

    def edge_source_target_vertices(self):
        edge_source_target_vertices = []
        for graph in self.graphs:
            edge_source_target_vertices.append(graph.edge_source_target_vertices())
        return edge_source_target_vertices

    def delete_edges(self, edges):
        # TODO check runtime
        for graph in self.graphs:
            for edge in edges:
                if graph.contains_vertices(edge):
                    graph.delete_edges([edge])

    def number_of_edges(self):
        number_of_edges = []
        for graph in self.graphs:
            number_of_edges.append(graph.number_of_edges())
        return number_of_edges

    def number_of_vertices(self):
        number_of_vertices = []
        for graph in self.graphs:
            number_of_vertices.append(graph.number_of_vertices())
        return number_of_vertices

    def vertices(self):
        vertices = []
        for graph in self.graphs:
            vertices.append(graph.vertices())
        return vertices

    def contains_vertices(self, vertices):
        for vertex in vertices:
            found = False
            for graph in self.graphs:

                if graph.contains_vertices([vertex]):
                    found = True
            if found is False:
                return False
        return True
