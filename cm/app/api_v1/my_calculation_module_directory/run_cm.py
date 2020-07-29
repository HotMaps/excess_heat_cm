import numpy as np
import os

from my_calculation_module_directory.dh_potential.CM_TUW4.polygonize import polygonize
from my_calculation_module_directory.dh_potential.CM_TUW0.rem_mk_dir import rm_mk_dir, rm_file
import my_calculation_module_directory.dh_potential.CM_TUW4.district_heating_potential as DHP
import my_calculation_module_directory.dh_potential.CM_TUW19.run_cm as CM19

from my_calculation_module_directory.excess_heat.excess_heat import excess_heat
from my_calculation_module_directory.excess_heat.utility import round_to_n
from my_calculation_module_directory.format import generate_graphics, round_indicators


def main(inputs_parameter_selection, inputs_raster_selection, industrial_database_excess_heat,
         output_raster1, output_raster2, output_shp1, output_shp2, output_transmission_lines):
    # The CM can be run for the following ranges of pixel and Dh thresholds:
    if inputs_parameter_selection["pix_threshold"] < 1:
        raise ValueError("Pixel threshold cannot be smaller than 1 GWh/km2!")
    if inputs_parameter_selection["DH_threshold"] < 1:
        raise ValueError("DH threshold cannot be smaller than 1 GWh/year!")

    # DH_Regions: boolean array showing DH regions
    DH_Regions, hdm_dh_region_cut, geo_transform, total_heat_demand = DHP.DHReg(inputs_raster_selection["heat"],
                                                                                inputs_parameter_selection["pix_threshold"],
                                                                                inputs_parameter_selection["DH_threshold"],
                                                                                None)

    DHPot, labels = DHP.DHPotential(DH_Regions, inputs_raster_selection["heat"])
    total_potential = np.around(np.sum(DHPot), 2)
    total_heat_demand = np.around(total_heat_demand, 2)
    if total_potential == 0:
        dh_area_flag = False
    else:
        dh_area_flag = True

    indicators = dict()
    graphics_data = dict()
    indicators["total_potential"] = total_potential
    graphics_data["DHPot"] = DHPot
    indicators["total_heat_demand"] = total_heat_demand

    if dh_area_flag:
        CM19.main(output_raster1, geo_transform, 'int8', DH_Regions)
        temp_raster = os.path.dirname(output_raster2) + '/temp.tif'
        CM19.main(temp_raster, geo_transform, 'int32', labels)
        symbol_vals_str = polygonize(output_raster1, temp_raster,
                                     output_shp1, output_shp2, DHPot)
        rm_file(temp_raster, temp_raster[:-4] + '.tfw')
        CM19.main(output_raster2, geo_transform, 'float32', hdm_dh_region_cut)

    else:
        return -1, "error: no dh area in selection"

    results = excess_heat(inputs_parameter_selection, inputs_raster_selection, industrial_database_excess_heat,
                          output_transmission_lines, output_raster1)
    if results[0] == -1:
        return results

    indicators_excess_heat, graphics_data_excess_heat, log_message = results
    indicators = {**indicators, **indicators_excess_heat}
    graphics_data = {**graphics_data, **graphics_data_excess_heat}

    indicators = round_indicators(indicators, 3)
    graphics = generate_graphics(inputs_parameter_selection, indicators, graphics_data)
    return indicators, graphics, log_message
