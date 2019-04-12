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
        raster_file_path = 'tests/data/heat_tot_curr_density_pilot_aera_1_aalborg.tif'
        # simulate copy from HTAPI to CM
        save_path = UPLOAD_DIRECTORY+"/raster_for_test.tif"
        copyfile(raster_file_path, save_path)

        inputs_raster_selection = {}
        inputs_parameter_selection = {}
        inputs_vector_selection = {}

        #with open('tests/data/data_hotmaps_task_2.7_load_profile_industry_chemicals_and_petrochemicals_yearlong_2018_dk.json', 'r') as file:
        #    inputs_vector_selection["load_profile_industry_chemicals_and_petrochemicals_yearlong_2018"] = json_lib.load(file)

        #with open('tests/data/data_hotmaps_task_2.7_load_profile_industry_food_and_tobacco_yearlong_2018_dk.json', 'r') as file:
        #    inputs_vector_selection["load_profile_industry_food_and_tobacco_yearlong_2018"] = json_lib.load(file)

        #with open('tests/data/data_hotmaps_task_2.7_load_profile_industry_iron_and_steel_yearlong_2018_dk.json', 'r') as file:
        #    inputs_vector_selection["load_profile_industry_iron_and_steel_yearlong_2018"] = json_lib.load(file)

        #with open('tests/data/data_hotmaps_task_2.7_load_profile_industry_non_metalic_minerals_yearlong_2018_dk.json', 'r') as file:
        #    inputs_vector_selection["load_profile_industry_non_metalic_minerals_yearlong_2018"] = json_lib.load(file)

        #with open('tests/data/data_hotmaps_task_2.7_load_profile_industry_paper_yearlong_2018_dk.json', 'r') as file:
        #    inputs_vector_selection["load_profile_industry_paper_yearlong_2018"] = json_lib.load(file)

        #with open('tests/data/data_hotmaps_task_2.7_load_profile_residential_heating_yearlong_2010_dk05.json', 'r') as file:
        #    inputs_vector_selection["load_profile_residential_heating_yearlong_2010"] = json_lib.load(file)

        #with open('tests/data/industrial_Database_dk.json', 'r') as file:
        #    inputs_vector_selection["industrial_database"] = json_lib.load(file)

        inputs_parameter_selection["search_radius"] = 20
        inputs_parameter_selection["investment_period"] = 10
        inputs_parameter_selection["transmission_line_threshold"] = 2


        inputs_parameter_selection["pix_threshold"] = 100
        inputs_parameter_selection["DH_threshold"] = 30

        inputs_raster_selection["heat"] = save_path

        # register the calculation module a
        payload = {"inputs_raster_selection": inputs_raster_selection,
                   "inputs_parameter_selection": inputs_parameter_selection,
                   "inputs_vector_selection": inputs_vector_selection}


        rv, json = self.client.post('computation-module/compute/', data=payload)

        self.assertTrue(rv.status_code == 200)


