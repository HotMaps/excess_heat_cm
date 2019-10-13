import unittest
from werkzeug.exceptions import NotFound
from app import create_app
import os.path
from shutil import copyfile
from .test_client import TestClient

import json as json_lib

UPLOAD_DIRECTORY = 'home/david/var/hotmaps/cm_files_uploaded'

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
        #raster_file_path = 'tests/data/pl22.tif'
        raster_file_path = "tests/data/heat_tot_curr_density_pilot_aera_1_aalborg.tif"
        # simulate copy from HTAPI to CM
        save_path = UPLOAD_DIRECTORY+"/heat_tot_curr_density_pilot_aera_1_aalborg.tif"
        copyfile(raster_file_path, save_path)

        inputs_raster_selection = {}
        inputs_parameter_selection = {}
        inputs_vector_selection = {}

        inputs_vector_selection["industrial_database"] = 'tests/data/industrial_Database_dk.json'

        inputs_parameter_selection["search_radius"] = 30
        inputs_parameter_selection["investment_period"] = 30
        inputs_parameter_selection["discount_rate"] = 0
        inputs_parameter_selection["cost_factor"] = 1
        inputs_parameter_selection["operational_costs"] = 0
        inputs_parameter_selection["transmission_line_threshold"] = 0.3
        inputs_parameter_selection["time_resolution"] = "month"
        inputs_parameter_selection["spatial_resolution"] = 2
        #nuts = ['PL22', 'PL21', "PL41", "PL42", "PL43", "PL51", "PL52", "CZ08"]
        nuts = ["DK05"]

        inputs_parameter_selection["pix_threshold"] = 100
        inputs_parameter_selection["DH_threshold"] = 30

        inputs_raster_selection["heat"] = save_path

        # register the calculation module
        payload = {"inputs_raster_selection": inputs_raster_selection,
                   "inputs_parameter_selection": inputs_parameter_selection,
                   "inputs_vector_selection": inputs_vector_selection,
                   "nuts": nuts}

        rv, json = self.client.post('computation-module/compute/', data=payload)
        has_indicators = False

        cm_name = json['result']['name']
        print ('cm_name ', type(cm_name))
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







        self.assertTrue(rv.status_code == 200)


