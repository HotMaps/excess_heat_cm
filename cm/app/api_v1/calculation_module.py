from osgeo import gdal
import os
import sys

from ..helper import generate_output_file_tif, create_zip_shapefiles, generate_output_file_shp
import time
""" Entry point of the calculation module function"""

from .my_calculation_module_directory import run_cm

""" Entry point of the calculation module function"""

#TODO: CM provider must "change this code"
#TODO: CM provider must "not change input_raster_selection,output_raster  1 raster input => 1 raster output"
#TODO: CM provider can "add all the parameters he needs to run his CM
#TODO: CM provider can "return as many indicators as he wants"
def calculation(output_directory, inputs_raster_selection, input_vector_selection, inputs_parameter_selection,nuts):
    """ def calculation()"""
    '''
    inputs:
        hdm in raster format for the selected region
        pix_threshold [GWh/km2]
        DH_threshold [GWh/a]

    Outputs:
        DH_Regions: contains binary values (no units) showing coherent areas
    '''
    input_raster_selection = inputs_raster_selection["heat"]

    pix_threshold = int(inputs_parameter_selection["pix_threshold"])
    DH_threshold = int(inputs_parameter_selection["DH_threshold"])

    search_radius = float(inputs_parameter_selection["search_radius"])
    investment_period = float(inputs_parameter_selection["investment_period"])
    transmission_line_threshold = float(inputs_parameter_selection["transmission_line_threshold"])

    nuts2_id = nuts
    print ('type nuts',type(nuts2_id))

    #industrial_sites = inputs_vector_selection["industrial_database"]

    #lp_chemical = inputs_vector_selection["load_profile_industry_chemicals_and_petrochemicals_yearlong_2018"]
    #lp_food = inputs_vector_selection["load_profile_industry_food_and_tobacco_yearlong_2018"]
    #lp_iron = inputs_vector_selection["load_profile_industry_iron_and_steel_yearlong_2018"]
    #lp_non_metalic = inputs_vector_selection["load_profile_industry_non_metalic_minerals_yearlong_2018"]
    #lp_paper = inputs_vector_selection["load_profile_industry_paper_yearlong_2018"]
    #industry_profiles = [lp_chemical, lp_food, lp_iron, lp_non_metalic, lp_paper]

    #sink_profiles = inputs_vector_selection["load_profile_residential_heating_yearlong_2010"]

    output_raster1 = generate_output_file_tif(output_directory)
    output_raster2 = generate_output_file_tif(output_directory)
    output_shp1 = generate_output_file_shp(output_directory)
    output_shp2 = generate_output_file_shp(output_directory)
    output_transmission_lines = generate_output_file_shp(output_directory)


    total_potential, total_heat_demand, graphics, total_cost_scalar, total_flow_scalar, total_cost_per_flow = \
                                                    run_cm.main(input_raster_selection,
                                                            pix_threshold,
                                                            DH_threshold,
                                                            output_raster1,
                                                            output_raster2,
                                                            output_shp1,
                                                            output_shp2,
                                                            search_radius,
                                                            investment_period,
                                                            transmission_line_threshold,
                                                            nuts2_id, output_transmission_lines)

    output_shp2 = create_zip_shapefiles(output_directory, output_shp2)
    output_transmission_lines = create_zip_shapefiles(output_directory, output_transmission_lines)
    result = dict()
    result['name'] = 'CM Excess Heat'
    result["raster_layers"]=[{"name": "district heating coherent areas","path": output_raster1, "type": "custom", "symbology": [{"red":250,"green":159,"blue":181,"opacity":0.8,"value":"1","label":"DH Areas"}]}]
    result["vector_layers"]=[{"name": "shapefile of coherent areas with their potential","path": output_shp2}, {"name": "Transmission lines as shapefile","path": output_transmission_lines}]

    if str(total_cost_per_flow) == "-inf" or "nan":
        result['indicator'] = [{"unit": "GWh", "name": "Total heat demand in GWh within the selected zone","value": str(total_heat_demand)},
                              {"unit": "GWh", "name": "Total district heating potential in GWh within the selected zone","value": str(total_potential)},
                               {"unit": "%",
                                "name": "Potential share of district heating from total demand in selected zone",
                                "value": str(100 * round(total_potential / total_heat_demand, 4))},
                               {"unit": "Euro", "name": "Cost of network",
                                "value": str(total_cost_scalar)},
                               {"unit": "GWh", "name": "Total annual flow of heat in the network",
                                "value": str(total_flow_scalar)},
                               {"unit": "ct/kWh/a", "name": "Cost of heat for selected investment period",
                                "value": str(total_cost_per_flow)}
                               ]
    else:
        result['indicator'] = [{"unit": "GWh", "name": "Total heat demand in GWh within the selected zone","value": str(total_heat_demand)},
                               {"unit": "GWh", "name": "Total district heating potential in GWh within the selected zone","value": str(total_potential)},
                               {"unit": "%",
                                "name": "Potential share of district heating from total demand in selected zone",
                                "value": str(100 * round(total_potential / total_heat_demand, 4))},
                               {"unit": "Euro", "name": "Cost of network",
                                "value": str(total_cost_scalar)},
                               {"unit": "GWh", "name": "Total annual flow of heat in the network",
                                "value": str(total_flow_scalar)},
                               ]

    result['graphics'] = graphics
    return result


def colorizeMyOutputRaster(out_ds):
    ct = gdal.ColorTable()
    ct.SetColorEntry(0, (0,0,0,255))
    ct.SetColorEntry(1, (110,220,110,255))
    out_ds.SetColorTable(ct)
    return out_ds
