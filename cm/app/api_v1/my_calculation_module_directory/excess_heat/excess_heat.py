import numpy as np
import pandas as pd
from itertools import repeat
from .read_data import ad_industrial_database_dict
from .read_data import ad_TUW23
from .read_data import ad_industry_profiles_local, ad_residential_heating_profile_local, ad_industrial_database_local
from .CM1 import find_neighbours, create_normalized_profiles, \
                cost_of_connection, cost_of_heat_exchanger_source, cost_of_heat_exchanger_sink, annuity_costs

from .visualisation import create_transmission_line_shp, round_to_n

from .graphs import NetworkGraph
from .logger import Logger

np.seterr(divide='ignore', invalid='ignore')


def excess_heat(sinks, search_radius, investment_period, discount_rate, cost_factor, operational_costs,
                transmission_line_threshold, heat_losses, time_resolution, spatial_resolution, nuts2_id,
                output_transmission_lines, industrial_sites_heat, industrial_sites_subsector):

    industrial_subsector_map = {"Iron and steel": "iron_and_steel", "Refineries": "chemicals_and_petrochemicals",
                                "Chemical industry": "chemicals_and_petrochemicals", "Cement": "non_metalic_minerals",
                                "Glass": "non_metalic_minerals",
                                "Non-metallic mineral products": "non_metalic_minerals", "Paper and printing": "paper",
                                "Non-ferrous metals": "iron_and_steel", "Other non-classified": "food_and_tobacco"}

    # if smaller than 730, 730 must be dividable by it
    time_resolution_map = {"hour": 1, "day": 10, "week": 146, "month": 730, "year": 8760}
    # number of time units to be averaged
    convolution_map = {"hour": 6, "day": 1, "week": 1, "month": 1, "year": 1}
    # factor for cost approximation network. Determines the peak performance compared to the yearly average
    peak_performance_map = {"hour": 2, "day": 2, "week": 2, "month": 2, "year": 1}

    # generate unique nuts 0 ids
    nuts0_id = []
    for id_ in nuts2_id:
        nuts0_id.append(id_[:2])

    # set time_resolution settings
    convolution = convolution_map[time_resolution]
    peak_performance = peak_performance_map[time_resolution]
    time_resolution = time_resolution_map[time_resolution]
    efficency = (1 - heat_losses/100)

    # create logger
    log = Logger()

    # load heat source and heat sink data
    #heat_sources = ad_industrial_database_dict(industrial_sites_heat, industrial_sites_subsector)
    heat_sources = ad_industrial_database_local(nuts2_id)
    heat_sinks = ad_TUW23(sinks, nuts2_id[0], spatial_resolution)

    # escape main routine if dh_potential cm did not produce shp file
    if not isinstance(heat_sinks, pd.DataFrame):
        log.add_error("No dh area in selection.")
        log_message = log.string_report()
        return -1, log_message

    # load heating profiles for sources and sinks
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
                log.add_warning("No industry profiles available for " + str(missing_profile) + ".")

    if heat_sources.shape[0] == 0:
        log.add_error("No industrial sites in selected area.")
        log_message = log.string_report()
        return -1, log_message

    # drop all sinks with unknown or invalid nuts id
    heat_sinks = heat_sinks[heat_sinks.Nuts2_ID != ""]
    heat_sinks = heat_sinks.dropna()
    missing_profiles = list(set(heat_sinks["Nuts2_ID"].unique()) -
                            set(normalized_heat_profiles["residential_heating"].keys()))
    for missing_profile in missing_profiles:
        heat_sinks = heat_sinks[heat_sinks.Nuts2_ID != missing_profile]
        log.add_warning("No residential heating profile available for " + str(missing_profile) + ".")

    if heat_sinks.shape[0] == 0:
        log.add_error("No entry points in selected area.")
        log_message = log.string_report()
        return -1, log_message

    # generate profiles at set time resolution for all heat sources and store them in an array
    heat_source_profiles = []
    heat_source_coordinates = []
    for _, heat_source in heat_sources.iterrows():
        reduced_profile = normalized_heat_profiles[
            industrial_subsector_map[heat_source["Subsector"]]][heat_source["Nuts0_ID"]]\
            .reshape(int(8760 / time_resolution), time_resolution)  # reshape profile to match time resolution setting
        reduced_profile = np.sum(reduced_profile, axis=1)
        heat_source_profiles.append(reduced_profile * float(heat_source["Excess_heat"]) * efficency)
        heat_source_coordinates.append((heat_source["Lon"], heat_source["Lat"]))
    heat_source_profiles = np.array(heat_source_profiles)
    heat_source_profiles = heat_source_profiles.transpose()

    # generate profiles at set time resolution for all heat sinks and store them in an array
    heat_sink_profiles = []
    heat_sink_coordinates = []
    for _, heat_sink in heat_sinks.iterrows():
        reduced_profile = normalized_heat_profiles["residential_heating"][heat_sink["Nuts2_ID"]]\
            .reshape(int(8760 / time_resolution), time_resolution)  # reshape profile to match time resolution setting
        reduced_profile = np.sum(reduced_profile, axis=1)
        heat_sink_profiles.append(reduced_profile * heat_sink["Heat_demand"])
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

    # if no source sink connections there can not be any flow
    if len([val for sublist in source_sink_connections for val in sublist]) == 0:
        log.add_error("No industrial sites in range.")
        log_message = log.string_report()
        return -1, log_message

    # build cost approximation network
    cost_approximation_network = NetworkGraph(source_sink_connections, source_source_connections, sink_sink_connections,
                                              range(len(source_source_connections)), heat_sinks["id"])
    cost_approximation_network.add_edge_attribute("distance", source_sink_distances, source_source_distances,
                                                  sink_sink_distances)
    # reduce to minimum spanning tree
    cost_approximation_network.reduce_to_minimum_spanning_tree("distance")

    # take yearly total of sites as capacity for the cost approximation network
    heat_source_capacities = heat_sources["Excess_heat"].tolist()
    heat_sink_capacities = heat_sinks["Heat_demand"].tolist()

    approximated_costs = []
    approximated_flows = []
    approximated_levelized_costs = []
    thresholds = []
    # remove most expensive transmission line until no lines are left
    while cost_approximation_network.return_number_of_edges() > 0:
        # recompute flow until its stable
        last_flows = [-1]
        while True:
            source_flow, sink_flow, connection_flow = cost_approximation_network.maximum_flow(heat_source_capacities,
                                                                                              heat_sink_capacities)
            connection_costs = []
            connection_lengths = cost_approximation_network.get_edge_attribute("distance")

            for flow, length in zip(connection_flow, connection_lengths):
                connection_costs.append(cost_of_connection(length, flow / 8760 * peak_performance, order=1))
            cost_per_connection = np.array(connection_costs)/np.abs(np.array(connection_flow)) / \
                investment_period * cost_factor

            heat_exchanger_source_costs = cost_of_heat_exchanger_source(source_flow / 8760 * peak_performance, order=1)
            heat_exchanger_sink_costs = cost_of_heat_exchanger_sink(sink_flow / 8760 * peak_performance, order=1)

            heat_exchanger_source_cost_total = np.sum(heat_exchanger_source_costs) * cost_factor
            heat_exchanger_sink_cost_total = np.sum(heat_exchanger_sink_costs) * cost_factor

            connection_cost_total = np.sum(connection_costs)
            # Euro
            total_cost_scalar = (heat_exchanger_sink_cost_total + heat_exchanger_source_cost_total +
                                 connection_cost_total)
            # GWh
            total_flow_scalar = np.sum(source_flow) / 1000

            # drop edges with 0 flow
            edges = cost_approximation_network.return_edge_source_target_vertices()
            for costs, edge in zip(cost_per_connection, edges):
                if costs < 0:
                    cost_approximation_network.delete_edges([edge])

            # stop if flow does not change anymore
            if np.sum(source_flow) == np.sum(last_flows):
                break
            last_flows = source_flow

        approximated_costs.append(total_cost_scalar)
        approximated_flows.append(total_flow_scalar)
        annuity = annuity_costs(total_cost_scalar, discount_rate / 100, investment_period)
        annual_cost_of_network = annuity + operational_costs / 100 * total_cost_scalar
        if total_flow_scalar > 0:
            levelised_cost_of_heat_supply = annual_cost_of_network / total_flow_scalar / 1e6 * 1e2  # ct/kWh
        else:
            levelised_cost_of_heat_supply = 0
        # check for zero divisions
        if total_flow_scalar == 0 and levelised_cost_of_heat_supply == 0:
            levelised_cost_of_heat_supply = 0
        else:
            if total_flow_scalar == 0:
                levelised_cost_of_heat_supply = 0

        approximated_levelized_costs.append(levelised_cost_of_heat_supply)

        # while there are still connections left delete the most expensive
        if len(cost_per_connection) > 0:
            thresholds.append(min(max(cost_per_connection), min(thresholds + [1e6])))
            most_expensive = list(cost_per_connection).index(max(cost_per_connection))
            cost_approximation_network.delete_edges([edges[most_expensive]])

    # add last threshold if non existent
    if len(thresholds) < len(approximated_costs):
        thresholds.append(0)

    thresholds = np.array(thresholds) / 1000 * 100  # convert euro/MWh to ct/kWh
    thresholds = thresholds.tolist()

    thresholds_y = []
    thresholds_y2 = []
    thresholds_y3 = []
    threshold_radius = []
    set_threshold = False
    for i, threshold in enumerate(thresholds):
        if threshold > transmission_line_threshold or set_threshold is True:
            thresholds_y.append(0)
            thresholds_y2.append(0)
            thresholds_y3.append(0)
            threshold_radius.append(0)
        else:
            thresholds_y.append(approximated_costs[i])
            thresholds_y2.append(approximated_levelized_costs[i])
            thresholds_y3.append(threshold)
            threshold_radius.append(3)
            set_threshold = True

    approximated_costs.reverse()
    approximated_flows.reverse()
    approximated_levelized_costs.reverse()
    thresholds.reverse()
    thresholds_y.reverse()
    thresholds_y2.reverse()
    thresholds_y3.reverse()
    threshold_radius.reverse()

    # network for exact computation of flow
    network = NetworkGraph(source_sink_connections, source_source_connections, sink_sink_connections,
                           range(len(source_source_connections)), heat_sinks["id"])
    network.add_edge_attribute("distance", source_sink_distances, source_source_distances, sink_sink_distances)
    # reduce to minimum spanning tree
    network.reduce_to_minimum_spanning_tree("distance")

    # compute max flow for every time unit
    last_flows = [-1]
    while True:
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
        connection_lengths = network.get_edge_attribute("distance")

        connection_costs = []
        for flow, length in zip(connection_flows, connection_lengths):
            connection_costs.append(cost_of_connection(length, flow / time_resolution, order=convolution))
        cost_per_connection = np.array(connection_costs)/np.array(np.sum(np.abs(connection_flows), axis=1)) / \
            investment_period * cost_factor

        # drop edges with 0 flow and above threshold
        edges = network.return_edge_source_target_vertices()
        for costs, edge in zip(cost_per_connection, edges):
            if costs < 0:
                network.delete_edges([edge])
        for costs, edge in zip(cost_per_connection, edges):
            if costs > transmission_line_threshold / 100 * 1000:    # convert ct/kwh to euro/mwh
                network.delete_edges([edge])

        # stop if flow does not change anymore
        if np.sum(source_flows) == np.sum(last_flows):
            break
        last_flows = source_flows

    # generate indicators
    heat_exchanger_source_costs = []
    for flow in source_flows:
        heat_exchanger_source_costs.append(cost_of_heat_exchanger_source(flow / time_resolution, order=convolution))
    heat_exchanger_sink_costs = []
    for flow in sink_flows:
        heat_exchanger_sink_costs.append(cost_of_heat_exchanger_sink(flow / time_resolution, order=convolution))

    heat_exchanger_source_cost_total = np.sum(heat_exchanger_source_costs) * cost_factor
    heat_exchanger_sink_cost_total = np.sum(heat_exchanger_sink_costs) * cost_factor

    connection_cost_total = np.sum(connection_costs)
    # Euro
    total_cost_scalar = (heat_exchanger_sink_cost_total + heat_exchanger_source_cost_total + connection_cost_total)
    # GWh
    total_flow_scalar = np.sum(source_flows) / 1000

    if total_flow_scalar == 0:
        log.add_error("No excess heat used.")
        log_message = log.string_report()
        return -1, log_message

    total_excess_heat_available = heat_sources["Excess_heat"].sum() / 1000  # GWh
    total_excess_heat_connected = 0

    for i, source_flow in enumerate(source_flows):
        # only consider sources which deliver heat
        if np.sum(source_flow) > 0:
            total_excess_heat_connected += heat_sources.iloc[i]["Excess_heat"]
    total_excess_heat_connected /= 1000  # GWh
    annuity = annuity_costs(total_cost_scalar, discount_rate/100, investment_period)
    annual_cost_of_network = annuity + operational_costs/100 * total_cost_scalar
    if total_flow_scalar > 0:
        levelised_cost_of_heat_supply = annual_cost_of_network / total_flow_scalar / 1e6 * 1e2  # ct/kWh
    else:
        levelised_cost_of_heat_supply = 0
    # check for zero divisions
    if total_flow_scalar == 0 and levelised_cost_of_heat_supply == 0:
        levelised_cost_of_heat_supply = 0
    else:
        if total_flow_scalar == 0:
            levelised_cost_of_heat_supply = 0
    # prepare hourly profiles for visualisation
    heat_source_profiles = heat_source_profiles.transpose()
    heat_sink_profiles = heat_sink_profiles.transpose()
    excess_heat_profile = np.zeros(int(8760 / time_resolution))
    for i, source_flow in enumerate(source_flows):
        # only consider sources which deliver heat
        if np.sum(source_flow) > 0:
            excess_heat_profile = excess_heat_profile + heat_source_profiles[i]
    heat_demand_profile = np.zeros(int(8760 / time_resolution))
    for i, sink_flow in enumerate(sink_flows):
        heat_demand_profile = heat_demand_profile + heat_sink_profiles[i]

    # reshape to monthly format if time resolution is at least monthly
    if time_resolution <= 730:
        excess_heat_profile_monthly = excess_heat_profile.reshape((12, int(730 / time_resolution)))
        heat_demand_profile_monthly = heat_demand_profile.reshape((12, int(730 / time_resolution)))
        # sum for every month
        excess_heat_profile_monthly = np.mean(excess_heat_profile_monthly, axis=1) / time_resolution
        heat_demand_profile_monthly = np.mean(heat_demand_profile_monthly, axis=1) / time_resolution
    else:
        excess_heat_profile_monthly = np.sum(excess_heat_profile) / 730 / 12 * np.array([1] * 12)
        heat_demand_profile_monthly = np.sum(heat_demand_profile) / 730 / 12 * np.array([1] * 12)

    # reshape to daily format if time resolution is at least daily
    if time_resolution <= 1:
        excess_heat_profile_daily = excess_heat_profile.reshape((365, 24))
        heat_demand_profile_daily = heat_demand_profile.reshape((365, 24))
        # sum for every hour of day
        excess_heat_profile_daily = np.mean(excess_heat_profile_daily, axis=0)
        heat_demand_profile_daily = np.mean(heat_demand_profile_daily, axis=0)
    else:
        excess_heat_profile_daily = np.sum(excess_heat_profile) / 365 / 24 * np.array([1] * 24)
        heat_demand_profile_daily = np.sum(excess_heat_profile) / 365 / 24 * np.array([1] * 24)

    excess_heat_profile_monthly = np.abs(excess_heat_profile_monthly)
    heat_demand_profile_monthly = np.abs(heat_demand_profile_monthly)
    excess_heat_profile_daily = np.abs(excess_heat_profile_daily)
    heat_demand_profile_daily = np.abs(heat_demand_profile_daily)
    excess_heat_profile_monthly = excess_heat_profile_monthly.tolist()
    heat_demand_profile_monthly = heat_demand_profile_monthly.tolist()
    excess_heat_profile_daily = excess_heat_profile_daily.tolist()
    heat_demand_profile_daily = heat_demand_profile_daily.tolist()

    # round to 3 significant digits
    excess_heat_profile_monthly = list(map(round_to_n, excess_heat_profile_monthly, repeat(3)))
    heat_demand_profile_monthly = list(map(round_to_n, heat_demand_profile_monthly, repeat(3)))
    excess_heat_profile_daily = list(map(round_to_n, excess_heat_profile_daily, repeat(3)))
    heat_demand_profile_daily = list(map(round_to_n, heat_demand_profile_daily, repeat(3)))

    approximated_costs = list(map(round_to_n, approximated_costs, repeat(3)))
    approximated_flows = list(map(round_to_n, approximated_flows, repeat(3)))
    approximated_levelized_costs = list(map(round_to_n, approximated_levelized_costs, repeat(3)))
    thresholds = list(map(round_to_n, thresholds, repeat(3)))
    thresholds_y = list(map(round_to_n, thresholds_y, repeat(3)))
    thresholds_y2 = list(map(round_to_n, thresholds_y2, repeat(3)))
    thresholds_y3 = list(map(round_to_n, thresholds_y3, repeat(3)))

    # catch any negative value
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

    total_excess_heat_available = round_to_n(total_excess_heat_available, 3)
    total_excess_heat_connected = round_to_n(total_excess_heat_connected, 3)
    total_flow_scalar = round_to_n(total_flow_scalar, 3)
    total_cost_scalar = round_to_n(total_cost_scalar, 3)
    annual_cost_of_network = round_to_n(annual_cost_of_network, 3)
    levelised_cost_of_heat_supply = round_to_n(levelised_cost_of_heat_supply, 3)

    # generate graphics
    coordinates = []
    for edge in network.return_edge_source_target_vertices():
        coordinates_of_line = []
        for point in edge:
            if point[0] == "source":
                coordinates_of_line.append((heat_sources.iloc[point[1]]["Lon"], heat_sources.iloc[point[1]]["Lat"]))
            else:
                coordinates_of_line.append((heat_sinks.iloc[point[1]]["Lon"], heat_sinks.iloc[point[1]]["Lat"]))

        coordinates.append(coordinates_of_line)
    temp = len(cost_per_connection) * [100]
    create_transmission_line_shp(coordinates, np.array(np.sum(connection_flows, axis=1)),  temp,
                                 np.abs(connection_costs), cost_per_connection, np.abs(connection_lengths), output_transmission_lines)

    log_message = log.string_report()

    return total_excess_heat_available, total_excess_heat_connected, total_flow_scalar, total_cost_scalar,\
        annual_cost_of_network, levelised_cost_of_heat_supply, excess_heat_profile_monthly,\
        heat_demand_profile_monthly, excess_heat_profile_daily, heat_demand_profile_daily, approximated_costs,\
        approximated_flows, thresholds, thresholds_y, thresholds_y2, thresholds_y3, threshold_radius,\
        approximated_levelized_costs, log_message
