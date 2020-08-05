import numpy as np
import pandas as pd
import rasterio

from my_calculation_module_directory.excess_heat.logger import Logger
from my_calculation_module_directory.excess_heat.read_data import ad_nuts_id, ad_industrial_database_local, ad_tuw23v2, ad_industry_profiles_local,\
    ad_residential_heating_profile_local
from my_calculation_module_directory.excess_heat.utility import create_normalized_profiles
from my_calculation_module_directory.excess_heat.parameters import *
from my_calculation_module_directory.excess_heat.dh_network.dh_network import DHNetwork


def excess_heat(inputs_parameter_selection, inputs_raster_selection, industrial_database_excess_heat,
            output_transmission_lines, output_raster1):
    heat_density_map = inputs_raster_selection["heat"]
    nuts_id_raster = inputs_raster_selection["nuts_id_number"]
    search_radius = 20000 #inputs_parameter_selection["search_radius"]
    investment_period = inputs_parameter_selection["investment_period"]
    discount_rate = inputs_parameter_selection["discount_rate"]
    transmission_line_threshold = inputs_parameter_selection["transmission_line_threshold"]
    time_resolution = inputs_parameter_selection["time_resolution"]
    #spatial_resolution = inputs_parameter_selection["spatial_resolution"]

    # create logger
    log = Logger()

    nuts_id_number = rasterio.open(nuts_id_raster)
    nuts_id_number = nuts_id_number.read()[0]
    nuts2_ids = []
    nuts_id_map = ad_nuts_id()
    nuts_ids = np.unique(nuts_id_number)
    for nuts_id in nuts_ids:
        if nuts_id != 0:  # don't consider areas with no nuts id
            nuts2_ids.append(nuts_id_map[nuts_id_map["id"] == nuts_id].values[0][1][0:4])

    # generate unique nuts 0 ids
    nuts0_id = []
    for id_ in nuts2_ids:
        nuts0_id.append(id_[:2])

    heat_sources = ad_industrial_database_local(nuts2_ids, industrial_database_excess_heat)
    heat_sinks = ad_tuw23v2(output_raster1, heat_density_map, nuts_id_raster)
    
    # escape main routine if dh_potential cm did not produce shp file
    if not isinstance(heat_sinks, pd.DataFrame):
        log.add_error("No dh area in selection.")
        log_message = log.string_report()
        return -1, log_message

    industry_profiles = ad_industry_profiles_local(nuts0_id)
    residential_heating_profile = ad_residential_heating_profile_local(nuts2_ids)

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
    for sub_sector in INDUSTRIAL_SUBSECTOR_MAP:
        missing_profiles = list(set(heat_sources[heat_sources.Subsector == sub_sector]["Nuts0_ID"].unique()) -
                                set(normalized_heat_profiles[INDUSTRIAL_SUBSECTOR_MAP[sub_sector]].keys()))
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
            INDUSTRIAL_SUBSECTOR_MAP[heat_source["Subsector"]]][heat_source["Nuts0_ID"]]\
            .reshape(int(8760 / TIME_RESOLUTION_MAP[time_resolution]), TIME_RESOLUTION_MAP[time_resolution])  # reshape profile to match time resolution setting
        reduced_profile = np.sum(reduced_profile, axis=1)
        heat_source_profiles.append(reduced_profile * float(heat_source["Excess_heat"]))
        heat_source_coordinates.append((heat_source["Lon"], heat_source["Lat"]))
    heat_source_profiles = np.array(heat_source_profiles)
    heat_source_profiles = heat_source_profiles.transpose()

    # generate profiles at set time resolution for all heat sinks and store them in an array
    heat_sink_profiles = []
    heat_sink_coordinates = []
    for _, heat_sink in heat_sinks.iterrows():
        reduced_profile = normalized_heat_profiles["residential_heating"][heat_sink["Nuts2_ID"]]\
            .reshape(int(8760 / TIME_RESOLUTION_MAP[time_resolution]), TIME_RESOLUTION_MAP[time_resolution])  # reshape profile to match time resolution setting
        reduced_profile = np.sum(reduced_profile, axis=1)
        heat_sink_profiles.append(reduced_profile * heat_sink["Heat_demand"])
        heat_sink_coordinates.append((heat_sink["Lon"], heat_sink["Lat"]))
    heat_sink_profiles = np.array(heat_sink_profiles)
    heat_sink_profiles = heat_sink_profiles.transpose()


    # print(heat_source_profiles.shape)
    # print(heat_sink_profiles.shape)
    # print(heat_sinks.id.values)

    #cost_approximation_network = DHNetwork(heat_sources, heat_sinks, [heat_sources["Excess_heat"].tolist()], [heat_sinks["Heat_demand"].tolist()])
    cost_approximation_network = DHNetwork(heat_sources, heat_sinks, heat_source_profiles, heat_sink_profiles)
    cost_approximation_network.time_unit = "year"
    cost_approximation_network.lifetime = investment_period
    cost_approximation_network.discount_rate = discount_rate
    cost_approximation_network.country = nuts0_id[0]
    cost_approximation_network.temperature = 100
    cost_approximation_network.fixed_radius_search(search_radius)
    cost_approximation_network.reduce_to_minimum_spanning_tree()
    cost_approximation_network.compute_flow()
    costs = []
    flows = []
    levelized_costs_of_heat_supply = []
    while cost_approximation_network.number_of_transmission_lines(mode="total") > 0:
        #print("lcoh: ", cost_approximation_network.levelized_cost_of_heat_supply(mode="total"))
        #cost_approximation_network.generate_shape_file(".test")
        costs.append(cost_approximation_network.remove_edge_with_highest_specific_cost(mode="total", return_costs=True))
        cost_approximation_network.compute_flow()
        flows.append(cost_approximation_network.heat_delivered(mode="total"))
        #print("delivered heat: ", cost_approximation_network.heat_delivered(mode="total"))
        levelized_costs_of_heat_supply.append(cost_approximation_network.levelized_cost_of_heat_supply(mode="total"))

    graphics_data = dict()
    #graphics_data["approximated_costs"] = costs
    #graphics_data["approximated_flows"] = flows
    #graphics_data["approximated_levelized_costs"] = levelized_costs_of_heat_supply

    network = DHNetwork(heat_sources, heat_sinks, heat_source_profiles, heat_sink_profiles)
    network.time_unit = time_resolution
    network.lifetime = investment_period
    network.discount_rate = discount_rate
    network.country = nuts0_id[0]
    network.temperature = 100

    network.fixed_radius_search(search_radius)
    if network.number_of_transmission_lines(mode="total") == 0:
        log.add_error("No industrial sites in range.")
        log_message = log.string_report()
        return -1, log_message
    network.reduce_to_minimum_spanning_tree()
    network.remove_lines_above_threshold_recursive(transmission_line_threshold)
    network.compute_flow()
    if network.heat_used(mode="total") == 0:
        log.add_error("No excess heat used.")
        log_message = log.string_report()
        return -1, log_message

    network.generate_shape_file(output_transmission_lines)
    indicators = dict()

    indicators["investment"] = network.compute_transmission_line_costs(typ="investment", mode="total")
    indicators["annuity"] = network.compute_transmission_line_costs(typ="annuity", mode="total")
    indicators["annual_cost"] = network.compute_transmission_line_costs(typ="annual_cost", mode="total")
    '''
    indicators["investment"] = network.total_costs(typ="investment", mode="total")
    indicators["annuity"] = network.total_costs(typ="annuity", mode="total")
    indicators["annual_cost"] = network.total_costs(typ="annual_cost", mode="total")
    '''
    indicators["heat_available"] = network.excess_heat_available()
    indicators["heat_connected"] = network.excess_heat_connected(mode="total")
    indicators["heat_used"] = network.heat_used(mode="total")
    indicators["heat_delivered"] = network.heat_delivered(mode="total")
    indicators["heat_lost"] = network.heat_lost(mode="total")
    #indicators["levelized_cost"] = network.levelized_cost_of_heat_supply(mode="total")
    indicators["levelized_cost"] = indicators["annual_cost"] / indicators["heat_delivered"]
    #indicators["maintenance_cost"] = network.total_costs(typ="operational_costs", mode="total")
    indicators["pump_energy_costs"] = network.pump_energy_costs(mode="total")

    graphics_data["excess_heat_profile"] = network.heat_profile("source", mode="total")
    graphics_data["heat_demand_profile"] = network.heat_profile("sink", mode="total")

    log_message = log.string_report()

    return indicators, graphics_data, log_message
