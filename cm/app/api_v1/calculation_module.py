from osgeo import gdal
from ..constant import CM_NAME
from ..helper import generate_output_file_tif, create_zip_shapefiles, generate_output_file_shp

""" Entry point of the calculation module function"""

from .my_calculation_module_directory import run_cm

""" Entry point of the calculation module function"""

# TODO: CM provider must "change this code"
# TODO: CM provider must "not change input_raster_selection,output_raster  1 raster input => 1 raster output"
# TODO: CM provider can "add all the parameters he needs to run his CM
# TODO: CM provider can "return as many indicators as he wants"


def calculation(output_directory, inputs_raster_selection, inputs_vector_selection, inputs_parameter_selection, nuts):
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
    discount_rate = float(inputs_parameter_selection["discount_rate"])
    cost_factor = float(inputs_parameter_selection["cost_factor"])
    operational_costs = float(inputs_parameter_selection["operational_costs"])
    transmission_line_threshold = float(inputs_parameter_selection["transmission_line_threshold"])

    time_resolution = inputs_parameter_selection["time_resolution"]
    spatial_resolution = float(inputs_parameter_selection["spatial_resolution"])

    nuts2_id = nuts
    print('type nuts', type(nuts2_id))

    industrial_sites = inputs_vector_selection["industrial_database"]

    output_raster1 = generate_output_file_tif(output_directory)
    output_raster2 = generate_output_file_tif(output_directory)
    output_shp1 = generate_output_file_shp(output_directory)
    output_shp2 = generate_output_file_shp(output_directory)
    output_transmission_lines = generate_output_file_shp(output_directory)

    results = run_cm.main(input_raster_selection, pix_threshold, DH_threshold, output_raster1, output_raster2,
                output_shp1, output_shp2, search_radius, investment_period, discount_rate, cost_factor,
                operational_costs, transmission_line_threshold, time_resolution, spatial_resolution,
                nuts2_id, output_transmission_lines, industrial_sites)

    if results[0] == -1:
        result = dict()
        result['name'] = CM_NAME
        result['indicator'] = [{"unit": " ", "name": "Log",
                            "value": results[1]}]
        return result

    total_potential, total_heat_demand, graphics, total_excess_heat_available, total_excess_heat_connected, \
    total_flow_scalar, total_cost_scalar, annual_cost_of_network, levelised_cost_of_heat_supply, log_message = results

    output_transmission_lines = create_zip_shapefiles(output_directory, output_transmission_lines)
    result = dict()

    # if graphics is not None:
    if total_potential > 0:
        output_shp2 = create_zip_shapefiles(output_directory, output_shp2)
        result["raster_layers"] = [{"name": "district heating coherent areas", "path": output_raster1, "type": "custom",
                                    "symbology": [{"red": 250, "green": 159, "blue": 181, "opacity": 0.8, "value": "1",
                                                   "label": "DH Areas"}]}]
        result["vector_layers"] = [{"name": "shapefile of coherent areas with their potential", "path": output_shp2},
                                   {"name": "Transmission lines as shapefile", "path": output_transmission_lines}]

    result['name'] = CM_NAME

    result['indicator'] = [{"unit": " ", "name": "Log", "value": log_message},
                           {"unit": "GWh", "name": "Total heat demand in GWh within the selected zone",
                            "value": str(total_heat_demand)},
                           {"unit": "GWh", "name": "Total district heating potential in GWh within the selected zone",
                            "value": str(total_potential)},
                           {"unit": "%",
                            "name": "Potential share of district heating from total demand in selected zone",
                            "value": str(100 * round(total_potential / total_heat_demand, 4))},
                           {"unit": "GWh", "name": "Excess heat available in selected area",
                            "value": str(total_excess_heat_available)},
                           {"unit": "GWh", "name": "Excess heat of sites connected to the network",
                            "value": str(total_excess_heat_connected)},
                           {"unit": "GWh", "name": "Excess heat used",
                            "value": str(total_flow_scalar)},
                           {"unit": "Euro", "name": "Investments necessary for network",
                            "value": str(total_cost_scalar)},
                           {"unit": "Euro/year", "name": "Annual costs of network",
                            "value": str(annual_cost_of_network)},
                           {"unit": "ct/kWh", "name": "Levelized cost of heat supply",
                            "value": str(levelised_cost_of_heat_supply)},
                           ]

    result['graphics'] = graphics
    return result


def colorizeMyOutputRaster(out_ds):
    ct = gdal.ColorTable()
    ct.SetColorEntry(0, (0,0,0,255))
    ct.SetColorEntry(1, (110,220,110,255))
    out_ds.SetColorTable(ct)
    return out_ds
