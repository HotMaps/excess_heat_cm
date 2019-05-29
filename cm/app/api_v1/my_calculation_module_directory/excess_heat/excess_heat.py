import numpy as np
import pandas as pd
from .read_data import ad_industrial_database_dict
from .read_data import ad_TUW23
from .read_data import ad_industry_profiles_dict
from .read_data import ad_residential_heating_profile_dict
from .read_data import ad_industry_profiles_local, ad_residential_heating_profile_local, ad_industrial_database_local
from .CM1 import find_neighbours, create_normalized_profiles, \
                cost_of_connection, cost_of_heat_exchanger_source, cost_of_heat_exchanger_sink, cost_after_discount

from .visualisation import create_transmission_line_shp

from .graphs import NetworkGraph


np.seterr(divide='ignore', invalid='ignore')


def excess_heat(sinks, search_radius, investment_period, discount_rate, cost_factor, operational_costs,
                transmission_line_threshold, nuts2_id, output_transmission_lines):

    industrial_subsector_map = {"Iron and steel": "iron_and_steel", "Refineries": "chemicals_and_petrochemicals",
                                "Chemical industry": "chemicals_and_petrochemicals", "Cement": "non_metalic_minerals",
                                "Glass": "non_metalic_minerals",
                                "Non-metallic mineral products": "non_metalic_minerals", "Paper and printing": "paper",
                                "Non-ferrous metals": "iron_and_steel", "Other non-classified": "food_and_tobacco"}

    nuts0_id = []
    for id in nuts2_id:
        nuts0_id.append(id[:2])


    # load heat source and heat sink data
    # heat_sources = ad_industrial_database_dict(sources)
    heat_sources = ad_industrial_database_local(nuts0_id)

    heat_sinks = ad_TUW23(sinks, nuts2_id[0])
    # escape main routine if dh_potential cm did not produce shp file
    if not isinstance(heat_sinks, pd.DataFrame):
        return 0, 0, 0
    # load heating profiles for sources and sinks
    # industry_profiles = ad_industry_profiles_dict(source_profiles)
    # residential_heating_profile = ad_residential_heating_profile_dict(sink_profiles)
    industry_profiles = ad_industry_profiles_local(nuts0_id)
    residential_heating_profile = ad_residential_heating_profile_local([nuts2_id[0]])

    # normalize loaded profiles
    normalized_heat_profiles = dict()
    normalized_heat_profiles["residential_heating"] = create_normalized_profiles(residential_heating_profile,
                                                                                 "NUTS2_code", "hour", "load")
    for industry_profile in industry_profiles:
        normalized_heat_profiles[industry_profile.iloc[1]["process"]] = \
            create_normalized_profiles(industry_profile, "NUTS0_code", "hour", "load")

    # drop all sources with unknown or invalid nuts id
    heat_sources = heat_sources[heat_sources.Nuts0_ID != ""]
    heat_sources = heat_sources.dropna()
    for sub_sector in industrial_subsector_map:
            missing_profiles = list(set(heat_sources[heat_sources.Subsector == sub_sector]["Nuts0_ID"].unique()) -
                                    set(normalized_heat_profiles[industrial_subsector_map[sub_sector]].keys()))
            for missing_profile in missing_profiles:
                heat_sources = heat_sources[((heat_sources.Nuts0_ID != missing_profile) |
                                             (heat_sources.Subsector != sub_sector))]

    # drop all sinks with unknown or invalid nuts id
    heat_sinks = heat_sinks[heat_sinks.Nuts2_ID != ""]
    heat_sinks = heat_sinks.dropna()
    missing_profiles = list(set(heat_sinks["Nuts2_ID"].unique()) -
                            set(normalized_heat_profiles["residential_heating"].keys()))
    for missing_profile in missing_profiles:
        heat_sinks = heat_sinks[heat_sinks.Nuts2_ID != missing_profile]

    # generate profiles for all heat sources and store them in an array
    heat_source_profiles = []
    heat_source_coordinates = []
    for _, heat_source in heat_sources.iterrows():
        heat_source_profiles.append(normalized_heat_profiles[industrial_subsector_map[heat_source["Subsector"]]]
                                    [heat_source["Nuts0_ID"]] * float(heat_source["Excess_heat"]))
        heat_source_coordinates.append((heat_source["Lon"], heat_source["Lat"]))
    heat_source_profiles = np.array(heat_source_profiles)
    heat_source_profiles = heat_source_profiles.transpose()

    # generate profiles for all heat sinks and store them in an array
    heat_sink_profiles = []
    heat_sink_coordinates = []
    for _, heat_sink in heat_sinks.iterrows():
        heat_sink_profiles.append(normalized_heat_profiles["residential_heating"][heat_sink["Nuts2_ID"]] *
                                  heat_sink["Heat_demand"])
        heat_sink_coordinates.append((heat_sink["Lon"], heat_sink["Lat"]))
    heat_sink_profiles = np.array(heat_sink_profiles)
    heat_sink_profiles = heat_sink_profiles.transpose()

    # find sites in search radius to build network graph
    temperature = 100
    source_sink_connections, source_sink_distances = find_neighbours(
        heat_sources, heat_sinks, "Lon", "Lat", "Lon", "Lat", "Temperature", "Temperature", search_radius,
        temperature, "true", "true", "true", small_angle_approximation=True)
    source_source_connections, source_source_distances = find_neighbours(
        heat_sources, heat_sources, "Lon", "Lat", "Lon", "Lat", "Temperature", "Temperature", search_radius,
        temperature, "true", "true", "true", small_angle_approximation=True)
    sink_sink_connections, sink_sink_distances = find_neighbours(
        heat_sinks, heat_sinks, "Lon", "Lat", "Lon", "Lat", "Temperature", "Temperature", search_radius,
        temperature, "true", "true", "true", small_angle_approximation=True)

    network = NetworkGraph(source_sink_connections, source_source_connections, sink_sink_connections,
                           range(len(source_source_connections)), heat_sinks["id"])
    network.add_edge_attribute("distance", source_sink_distances, source_source_distances, sink_sink_distances)
    # reduce to minimum spanning tree
    network.reduce_to_minimum_spanning_tree("distance")

    # compute max flow for every hour
    def compute_flow(network, heat_source_profiles, heat_sink_profiles):
        source_flows = []
        sink_flows = []
        connection_flows = []
        for heat_source_capacities, heat_sink_capacities in zip(heat_source_profiles, heat_sink_profiles):
            source_flow, sink_flow, connection_flow = network.maximum_flow(heat_source_capacities, heat_sink_capacities)
            source_flows.append(source_flow)
            sink_flows.append(sink_flow)
            connection_flows.append(connection_flow)

        source_flows = np.abs(np.array(source_flows))
        sink_flows = np.abs(np.array(sink_flows))
        connection_flows = np.abs(np.array(connection_flows))
        source_flows = source_flows.transpose()
        sink_flows = sink_flows.transpose()
        connection_flows = connection_flows.transpose()

        # compute costs of every heat exchanger and transmission line
        heat_exchanger_source_costs = []
        for flow in source_flows:
            heat_exchanger_source_costs.append(cost_of_heat_exchanger_source(flow))
        heat_exchanger_sink_costs = []
        for flow in sink_flows:
            heat_exchanger_sink_costs.append(cost_of_heat_exchanger_sink(flow))
        connection_lengths = network.get_edge_attribute("distance")
        connection_costs = []
        for flow, length in zip(connection_flows, connection_lengths):
            connection_costs.append(cost_of_connection(length, flow))
        cost_per_connection = np.array(connection_costs)/np.array(np.sum(connection_flows, axis=1)) / investment_period

        # compute total costs and flow of network
        heat_exchanger_source_cost_total = np.sum(heat_exchanger_source_costs)
        heat_exchanger_sink_cost_total = np.sum(heat_exchanger_sink_costs)
        connection_cost_total = np.sum(connection_costs)
        # Euro
        total_cost_scalar = (heat_exchanger_sink_cost_total + heat_exchanger_source_cost_total + connection_cost_total)
        # GWh
        total_flow_scalar = np.sum(source_flows)/1000

        # ct/kWh
        total_cost_per_flow = total_cost_scalar/total_flow_scalar/investment_period/1e6*1e2

        return source_flows, sink_flows, connection_flows, connection_costs, connection_lengths, cost_per_connection, total_cost_scalar, total_flow_scalar, total_cost_per_flow


    source_flows, sink_flows, connection_flows, connection_costs, connection_lengths, cost_per_connection,\
    total_cost_scalar, total_flow_scalar, total_cost_per_flow = compute_flow(network, heat_source_profiles, heat_sink_profiles)
    last_flows = [-1]
    while np.sum(source_flows) != np.sum(last_flows):
        last_flows = source_flows
        # drop egdes with 0 flow and above threshold
        edges = network.return_edge_source_target_vertices()
        for costs, edge in zip(cost_per_connection, edges):
            if costs < 0:
                network.delete_edges([edge])
        for costs, edge in zip(cost_per_connection, edges):
            if costs > transmission_line_threshold:
                network.delete_edges([edge])
        source_flows, sink_flows, connection_flows, connection_costs, connection_lengths, cost_per_connection,\
        total_cost_scalar, total_flow_scalar, total_cost_per_flow = compute_flow(network, heat_source_profiles, heat_sink_profiles)

    # generate output graphics and indicators
    coordiantes = []
    for edge in network.return_edge_source_target_vertices():
        coordiantes_of_line = []
        for point in edge:
            if point[0] == "source":
                coordiantes_of_line.append((heat_sources.iloc[point[1]]["Lon"], heat_sources.iloc[point[1]]["Lat"]))
            else:
                coordiantes_of_line.append((heat_sinks.iloc[point[1]]["Lon"], heat_sinks.iloc[point[1]]["Lat"]))

        coordiantes.append(coordiantes_of_line)
    temp = len(cost_per_connection) * [100]
    create_transmission_line_shp(coordiantes, np.array(np.sum(connection_flows, axis=1)),  temp, connection_costs, connection_lengths,
                                 output_transmission_lines)

    total_excess_heat_available = heat_sources["Excess_heat"].sum() / 1000  # GWh
    total_excess_heat_connected = 0
    for i, source_flow in enumerate(source_flows):
        if np.sum(source_flow) > 0:
            total_excess_heat_connected += heat_sources.iloc[i]["Excess_heat"]
    total_excess_heat_connected /= 1000  # GWh
    cost_with_discount = cost_after_discount(total_cost_scalar, discount_rate/100, investment_period)
    annual_cost_of_network = cost_with_discount / investment_period + operational_costs/100 * total_cost_scalar
    levelised_cost_of_heat_supply = annual_cost_of_network / total_flow_scalar / 1e6 * 1e2  # ct/kWh
    if total_flow_scalar == 0 and levelised_cost_of_heat_supply == 0:
        levelised_cost_of_heat_supply = 0
    else:
        if total_flow_scalar == 0:
            levelised_cost_of_heat_supply = 0

    heat_source_profiles = heat_source_profiles.transpose()
    heat_sink_profiles = heat_sink_profiles.transpose()

    excess_heat_profile = np.zeros(8760)
    for i, source_flow in enumerate(source_flows):
        if np.sum(source_flow) > 0:
            excess_heat_profile = excess_heat_profile + heat_source_profiles[i]

    heat_demand_profile = np.zeros(8760)
    for i, sink_flow in enumerate(sink_flows):
        heat_demand_profile = heat_demand_profile + heat_sink_profiles[i]

    excess_heat_profile_monthly = excess_heat_profile.reshape((12, 730))
    heat_demand_profile_monthly = heat_demand_profile.reshape((12, 730))

    excess_heat_profile_daily = excess_heat_profile.reshape((365, 24))
    heat_demand_profile_daily = heat_demand_profile.reshape((365, 24))

    # sum for every month
    excess_heat_profile_monthly = np.mean(excess_heat_profile_monthly, axis=1)
    heat_demand_profile_monthly = np.mean(heat_demand_profile_monthly, axis=1)

    # sum for every day hour
    excess_heat_profile_daily = np.mean(excess_heat_profile_daily, axis=0)
    heat_demand_profile_daily = np.mean(heat_demand_profile_daily, axis=0)

    excess_heat_profile_monthly = excess_heat_profile_monthly.tolist()
    heat_demand_profile_monthly = heat_demand_profile_monthly.tolist()
    excess_heat_profile_daily = excess_heat_profile_daily.tolist()
    heat_demand_profile_daily = heat_demand_profile_daily.tolist()

    if total_excess_heat_available < 0:
        total_excess_heat_available = 0
    if total_excess_heat_connected < 0:
        total_excess_heat_connected = 0
    if total_flow_scalar < 0:
        total_flow_scalar = 0
    if total_cost_scalar < 0:
        total_flow_scalar = 0
    if annual_cost_of_network < 0:
        annual_cost_of_network = 0
    if levelised_cost_of_heat_supply < 0:
        levelised_cost_of_heat_supply = 0

    return total_excess_heat_available, total_excess_heat_connected, total_flow_scalar, total_cost_scalar,\
        annual_cost_of_network, levelised_cost_of_heat_supply, excess_heat_profile_monthly,\
        heat_demand_profile_monthly, excess_heat_profile_daily, heat_demand_profile_daily
