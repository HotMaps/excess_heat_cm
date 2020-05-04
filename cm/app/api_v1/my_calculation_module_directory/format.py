import numpy as np
from itertools import repeat
from .excess_heat.utility import round_to_n
from .excess_heat.parameters import *


def generate_graphics(parameters, indicators, graphics_data):
    total_heat_demand = indicators["total_heat_demand"]
    total_potential = indicators["total_heat_demand"]
    total_excess_heat_available = indicators["heat_available"]
    total_excess_heat_connected = indicators["heat_connected"]
    heat_used = indicators["heat_used"]
    heat_delivered = indicators["heat_delivered"]

    time_resolution = parameters["time_resolution"]
    time_resolution = TIME_RESOLUTION_MAP[time_resolution]
    transmission_line_threshold = parameters["transmission_line_threshold"]

    excess_heat_profile = graphics_data["excess_heat_profile"]
    heat_demand_profile = graphics_data["heat_demand_profile"]
    dhpot = graphics_data["DHPot"]

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

    excess_heat_profile_monthly = excess_heat_profile_monthly.tolist()
    heat_demand_profile_monthly = heat_demand_profile_monthly.tolist()
    excess_heat_profile_daily = excess_heat_profile_daily.tolist()
    heat_demand_profile_daily = heat_demand_profile_daily.tolist()

    thresholds = np.array(graphics_data["approximated_costs"]) / 1000 * 100  # convert euro/MWh to ct/kWh
    thresholds = thresholds.tolist()
    approximated_levelized_costs = graphics_data["approximated_levelized_costs"]
    approximated_flows = graphics_data["approximated_flows"]

    set_lcoh = []
    set_thresholds = []
    set_radius = []
    set_threshold = False
    for i, threshold in enumerate(thresholds):
        if threshold > transmission_line_threshold or set_threshold is True:
            set_lcoh.append(0)
            set_thresholds.append(0)
            set_radius.append(0)
        else:
            set_lcoh.append(approximated_levelized_costs[i])
            set_thresholds.append(threshold)
            set_radius.append(3)
            set_threshold = True

    approximated_flows.reverse()
    approximated_levelized_costs.reverse()
    thresholds.reverse()
    set_lcoh.reverse()
    set_thresholds.reverse()
    set_radius.reverse()

    dhpot = round_list(dhpot, 3)
    approximated_flows = round_list(approximated_flows, 3)
    approximated_levelized_costs = round_list(approximated_levelized_costs, 3)
    thresholds = np.array(thresholds)
    thresholds[np.isinf(thresholds)] = 0
    thresholds = round_list(thresholds.tolist(), 3)
    set_lcoh = round_list(set_lcoh, 3)
    set_thresholds = round_list(set_thresholds, 3)
    excess_heat_profile_monthly = round_list(excess_heat_profile_monthly, 3)
    heat_demand_profile_monthly = round_list(heat_demand_profile_monthly, 3)
    excess_heat_profile_daily = round_list(excess_heat_profile_daily, 3)
    heat_demand_profile_daily = round_list(heat_demand_profile_daily, 3)

    graphics_json = [
        {
            "type": "bar",
            "xLabel": "DH Area Label",
            "yLabel": "Potential (GWh/year)",
            "data": {
                "labels": [str(x) for x in range(1, 1 + len(dhpot))],
                "datasets": [{
                    "label": "Potential in coherent areas",
                    "backgroundColor": ["#3e95cd"] * len(dhpot),
                    "data": list(np.around(dhpot, 2))
                }]
            }
        },
        {
            "type": "bar",
            "xLabel": "",
            "yLabel": "Energy per year (GWh/year)",
            "data": {
                "labels": ["Annual heat demand", "DH potential", "Total excess heat available",
                           "Total excess heat from connected sites", "Excess heat used", "Excess heat delivered"],
                "datasets": [{
                    "label": "Heat Demand and Excess heat",
                    "backgroundColor": ["#3e95cd", "#3e95cd", "#fe7c60", "#fe7c60", "#fe7c60", "#fe7c60"],
                    "data": [total_heat_demand, total_potential, total_excess_heat_available,
                             total_excess_heat_connected, heat_used, ]
                }]
            }
        },
        {
            "type": "line",
            "xLabel": "Annual delivered excess heat in GWh",
            "yLabel": "Costs in ct/kWh",
            "data": {
                "labels": [str(x) for x in approximated_flows],
                "datasets": [{
                    "label": "Set transmission line threshold",
                    "data": set_lcoh,
                    "pointRadius": set_radius,
                    "borderColor": "#fe7c60",
                    "pointBackgroundColor": "#fe7c60",
                    "showLine": False
                }, {
                    "label": "Set transmission line threshold",
                    "data": set_threshold,
                    "pointRadius": set_radius,
                    "borderColor": "#fe7c60",
                    "pointBackgroundColor": "#fe7c60",
                    "showLine": False
                },
                    {
                        "label": "levelized cost",
                        "data": approximated_levelized_costs,
                        "borderColor": "#3e95cd",
                    }, {
                        "label": "Transmission line threshold",
                        "data": thresholds,
                        "borderColor": "#32CD32",
                    }
                ]
            }
        },
        {
            "type": "line",
            "xLabel": "Month",
            "yLabel": "Demand / Excess in MW",
            "data": {
                "labels": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                           "October", "November", "December"],
                "datasets": [{
                    "label": "Heat demand",
                    "borderColor": "#3e95cd",
                    "backgroundColor": "rgba(62, 149, 205, 0.35)",
                    "data": heat_demand_profile_monthly
                }, {
                    "label": "Excess heat",
                    "borderColor": "#fe7c60",
                    "backgroundColor": "rgba(254, 124, 96, 0.35)",
                    "data": excess_heat_profile_monthly
                }]
            }
        },
        {
            "type": "line",
            "xLabel": "Day hour",
            "yLabel": "Demand / Excess in MW",
            "data": {
                "labels": [str(x) for x in range(1, 25)],
                "datasets": [{
                    "label": "Heat demand",
                    "borderColor": "#3e95cd",
                    "backgroundColor": "rgba(62, 149, 205, 0.35)",
                    "data": heat_demand_profile_daily
                }, {
                    "label": "Excess heat",
                    "borderColor": "#fe7c60",
                    "backgroundColor": "rgba(254, 124, 96, 0.35)",
                    "data": excess_heat_profile_daily
                }]
            }
        }
    ]
    return graphics_json


def round_indicators(indicators, n):
    for indicator in indicators:
        indicators[indicator] = round_to_n(indicators[indicator], n)
    return indicators


def round_list(list_to_round, n):
    return list(map(round_to_n, list_to_round, repeat(n)))
