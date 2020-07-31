import unittest
from werkzeug.exceptions import NotFound
from app import create_app
import os.path
from shutil import copyfile
from .test_client import TestClient

import json as json_lib

UPLOAD_DIRECTORY = '/var/hotmaps/cm_files_uploaded'

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    os.chmod(UPLOAD_DIRECTORY, 0o777)


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.app = create_app(os.environ.get('FLASK_CONFIG', 'development'))
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.client = TestClient(self.app,)

    def tearDown(self):
        self.ctx.pop()

    def test_compute(self):
        pp = 'tests/data'
        raster_file_path = pp + '/test_heat_tot_curr_density.tif'
        # simulate copy from HTAPI to CM
        save_path = UPLOAD_DIRECTORY+"/test_heat_tot_curr_density.tif"
        copyfile(raster_file_path, save_path)

        inputs_raster_selection = {}
        inputs_parameter_selection = {}
        inputs_vector_selection = {}

        inputs_vector_selection["industrial_database_excess_heat"] = pp + '/test_industrial_database_excess_heat.csv'
        inputs_vector_selection["industrial_database_subsector"] = pp + '/test_industrial_database_subsector.csv'
        
        #inputs_parameter_selection["search_radius"] = 20
        inputs_parameter_selection["investment_period"] = 30
        inputs_parameter_selection["discount_rate"] = 3
        inputs_parameter_selection["cost_factor"] = 1
        inputs_parameter_selection["operational_costs"] = 1
        inputs_parameter_selection["heat_losses"] = 20
        inputs_parameter_selection["transmission_line_threshold"] = 20
        inputs_parameter_selection["time_resolution"] = "week"
        inputs_parameter_selection["spatial_resolution"] = 2
        #nuts = ['PL22', 'PL21', "PL41", "PL42", "PL43", "PL51", "PL52", "CZ08"]
        #nuts = ["DK05"]

        inputs_parameter_selection["pix_threshold"] = 555
        inputs_parameter_selection["DH_threshold"] = 30

        inputs_raster_selection["heat"] = save_path
        inputs_raster_selection["nuts_id_number"] = pp + "/test_nuts_id_number.tif"

        # register the calculation module
        payload = {"inputs_raster_selection": inputs_raster_selection,
                   "inputs_parameter_selection": inputs_parameter_selection,
                   "inputs_vector_selection": inputs_vector_selection,
                   }

        rv, json = self.client.post('computation-module/compute/', data=payload)
        '''
        has_indicators = False

        cm_name = json['result']['name']
        try:
            indicators = json['result']['indicator']
            has_indicators = True

        except:
            pass
        #test is the value are string
        if has_indicators == True:
            for ind in indicators:
                value = ind['value']
                print ('value ', type(value))
                self.assertIs(type(value), str)
        if has_indicators == True:
            for ind in indicators:
                value = ind['value']
                print ('value ', type(value))
                self.assertTrue(value != -888888888)
        '''
        self.assertTrue(rv.status_code == 200)
