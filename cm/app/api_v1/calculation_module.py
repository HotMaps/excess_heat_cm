import os
import sys
import pandas as pd

path = os.path.dirname(os.path.abspath(__file__))
from ..constant import CM_NAME
from ..helper import generate_output_file_tif, create_zip_shapefiles, generate_output_file_shp, generate_output_file_csv

""" Entry point of the calculation module function"""
if path not in sys.path:
    sys.path.append(path)
from my_calculation_module_directory import run_cm

""" Entry point of the calculation module function"""


# TODO: CM provider must "change this code"
# TODO: CM provider must "not change input_raster_selection,output_raster  1 raster input => 1 raster output"
# TODO: CM provider can "add all the parameters he needs to run his CM
# TODO: CM provider can "return as many indicators as he wants"

def merge_industry_subsector(industrial_database_excess_heat, industrial_database_subsector, ind_out_csv):
    """merge industrial site and subsector csv layers"""
    #df1 = pd.read_csv(industrial_database_excess_heat, encoding='latin1').drop_duplicates(subset=['geometry_wkt'])
    df1 = pd.read_csv(industrial_database_excess_heat, encoding='latin1')
    #df2 = pd.read_csv(industrial_database_subsector, encoding='latin1').drop_duplicates(subset=['geometry_wkt'])
    df2 = pd.read_csv(industrial_database_subsector, encoding='latin1')
    print("################ Columns excess heat: ", df1.columns)
    print("################ Columns subsector: ", df2.columns)
    df2 = df2.drop_duplicates(subset=['geometry_wkt'])
    df = df1.merge(df2, on='geometry_wkt', how='left',
                   suffixes=('', '_right')).drop_duplicates(subset=['geometry_wkt',
                                                                    'excess_heat_100_200c',
                                                                    'excess_heat_200_500c',
                                                                    'excess_heat_500c'])
    if df.shape[0] > 0:
        flag = False
    else:
        flag = True
    df.to_csv(ind_out_csv, index=False, encoding='latin1')
    return flag


def calculation(output_directory, inputs_raster_selection, inputs_vector_selection, inputs_parameter_selection):
    """ def calculation()"""
    '''
    inputs:
        hdm in raster format for the selected region
        pix_threshold [GWh/km2]
        DH_threshold [GWh/a]
    Outputs:
        DH_Regions: contains binary values (no units) showing coherent areas
    # ###############
    '''
    inputs_parameter_selection["pix_threshold"] = int(inputs_parameter_selection["pix_threshold"])
    inputs_parameter_selection["DH_threshold"] = int(inputs_parameter_selection["DH_threshold"])
    # inputs_parameter_selection["search_radius"] = float(inputs_parameter_selection["search_radius"]) * 1000
    inputs_parameter_selection["investment_period"] = float(inputs_parameter_selection["investment_period"])
    inputs_parameter_selection["discount_rate"] = float(inputs_parameter_selection["discount_rate"]) / 100
    inputs_parameter_selection["cost_factor"] = float(inputs_parameter_selection["cost_factor"])
    inputs_parameter_selection["operational_costs"] = float(inputs_parameter_selection["operational_costs"]) / 100
    inputs_parameter_selection["transmission_line_threshold"] = \
        float(inputs_parameter_selection["transmission_line_threshold"]) * 10  # convert from ct/kWh to euro/MWh
    # inputs_parameter_selection["spatial_resolution"] = float(inputs_parameter_selection["spatial_resolution"])

    industrial_database_excess_heat = inputs_vector_selection['industrial_database_excess_heat']
    industrial_database_subsector = inputs_vector_selection['industrial_database_subsector']

    ind_out_csv = generate_output_file_csv(output_directory)
    output_raster1 = generate_output_file_tif(output_directory)
    output_raster2 = generate_output_file_tif(output_directory)
    output_shp1 = generate_output_file_shp(output_directory)
    output_shp2 = generate_output_file_shp(output_directory)
    output_transmission_lines = generate_output_file_shp(output_directory)




    result = dict()
    flag = merge_industry_subsector(industrial_database_excess_heat, industrial_database_subsector, ind_out_csv)
    if flag:
        result['name'] = CM_NAME
        result['indicator'] = [
            {"unit": " ", "name": "Error! Check industrial excess heat and industrial subset data sets.",
             "value": "0"}]
        return result

    results = run_cm.main(inputs_parameter_selection, inputs_raster_selection, ind_out_csv,
                          output_raster1, output_raster2, output_shp1, output_shp2, output_transmission_lines)
    if results[0] == -1:
        result['name'] = CM_NAME
        result['indicator'] = [{"unit": " ", "name": results[1],
                                "value": "0"}]
        return result

    indicators, graphics, log_message = results

    output_transmission_lines = create_zip_shapefiles(output_directory, output_transmission_lines)

    # if graphics is not None:
    if indicators["total_potential"] > 0:
        output_shp2 = create_zip_shapefiles(output_directory, output_shp2)
        result["raster_layers"] = [{"name": "district heating coherent areas", "path": output_raster1, "type": "custom",
                                    "symbology": [{"red": 250, "green": 159, "blue": 181, "opacity": 0.8, "value": "1",
                                                   "label": "DH Areas"}]}]
        result["vector_layers"] = [{"name": "shapefile of coherent areas with their potential", "path": output_shp2},
                                   {"name": "Transmission lines as shapefile", "path": output_transmission_lines}]

    result['name'] = CM_NAME
    result['indicator'] = [{"unit": "GWh", "name": "Total heat demand in GWh within the selected zone",
                            "value": str(indicators["total_heat_demand"])},
                           {"unit": "GWh", "name": "Total district heating potential in GWh within the selected zone",
                            "value": str(indicators["total_potential"])},
                           {"unit": "%",
                            "name": "Potential share of district heating from total demand in selected zone",
                            "value": str(100 * round(indicators["total_potential"] / indicators["total_heat_demand"],
                                                     4))},
                           {"unit": "GWh", "name": "Excess heat available in selected area",
                            "value": str(indicators["heat_available"] / 1000)},
                           {"unit": "GWh", "name": "Excess heat of sites connected to the network",
                            "value": str(indicators["heat_connected"] / 1000)},
                           {"unit": "GWh", "name": "Excess heat used",
                            "value": str(indicators["heat_used"] / 1000)},
                           {"unit": "GWh", "name": "Excess heat delivered",
                            "value": str(indicators["heat_delivered"] / 1000)},
                           {"unit": "GWh", "name": "Heat loss",
                            "value": str(indicators["heat_lost"] / 1000)},
                           # {"unit": "Euro", "name": "Pump energy costs",
                           #  "value": str(indicators["pump_energy_costs"])},
                           # {"unit": "Euro", "name": "Maintenance cost",
                           #  "value": str(indicators["maintenance_cost"])},
                           {"unit": "Euro", "name": "Investments necessary for network",
                            "value": str(indicators["investment"])},
                           {"unit": "Euro/yr", "name": "Annual costs of network",
                            "value": str(indicators["annual_cost"])},
                           {"unit": "ct/kWh", "name": "Levelized cost of heat supply",
                            "value": str(indicators["levelized_cost"] / 10)},
                           ]

    if log_message != "":
        result['indicator'].insert(0, {"unit": " ", "name": log_message, "value": "0"})
    result['graphics'] = graphics

    return result
