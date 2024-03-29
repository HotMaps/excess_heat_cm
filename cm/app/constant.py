
CELERY_BROKER_URL_DOCKER = 'amqp://admin:mypass@rabbit:5672/'
CELERY_BROKER_URL_LOCAL = 'amqp://localhost/'



CM_REGISTER_Q = 'rpc_queue_CM_register'
CM_NAME = 'CM - Excess heat transport potential'
RPC_CM_ALIVE= 'rpc_queue_CM_ALIVE'
RPC_Q = 'rpc_queue_CM_compute' # Do no change this value
CM_ID = 7
PORT_LOCAL = int('500' + str(CM_ID))
PORT_DOCKER = 80
#TODO***********************************************************************
CELERY_BROKER_URL = CELERY_BROKER_URL_DOCKER
PORT = PORT_DOCKER
#TODO***********************************************************************

TRANFER_PROTOCOLE ='http://'

INPUTS_CALCULATION_MODULE = [

    {'input_name': 'Min. heat demand in hectare',
     'input_type': 'input',

     'input_parameter_name': 'pix_threshold',
     'input_value': 333,
     'input_unit': 'MWh/(ha*yr)',
     'input_priority': 0,
     'input_min': 0,
     'input_max': 1000,
     'cm_id': CM_ID
     },
    {'input_name': 'Min. heat demand in a DH area',
     'input_type': 'input',
     'input_parameter_name': 'DH_threshold',
     'input_value': 30,
     'input_unit': 'GWh/yr',
     'input_min': 0,
     'input_max': 500,
     'cm_id': CM_ID
     },
    #{'input_name': 'Maximum search radius',
    # 'input_type': 'input',
    # 'input_parameter_name': 'search_radius',
    # 'input_value': 20,
    # 'input_unit': 'km',
    # 'input_min': 0,
    # 'input_max': 100,
    # 'cm_id': CM_ID
    #},
    {'input_name': 'Lifetime of equipment',
     'input_type': 'input',
     'input_parameter_name': 'investment_period',
     'input_value': 30,
     'input_unit': 'year',
     'input_min': 10,
     'input_max': 60,
     'cm_id': CM_ID
     },
    {'input_name': 'Discount rate',
     'input_type': 'input',
     'input_parameter_name': 'discount_rate',
     'input_value': 3,
     'input_unit': '%',
     'input_min': 0,
     'input_max': 20,
     'cm_id': CM_ID
     },
    {'input_name': 'Cost factor',
     'input_type': 'input',
     'input_parameter_name': 'cost_factor',
     'input_value': 1,
     'input_unit': '',
     'input_min': 0.1,
     'input_max': 10,
     'cm_id': CM_ID
     },
    {'input_name': 'Operational costs',
     'input_type': 'input',
     'input_parameter_name': 'operational_costs',
     'input_value': 2,
     'input_unit': '%',
     'input_min': 0,
     'input_max': 10,
     'cm_id': CM_ID
     },
    {'input_name': 'Transmission line threshold',
     'input_type': 'input',
     'input_parameter_name': 'transmission_line_threshold',
     'input_value': 0.5,
     'input_unit': 'ct/kWh/yr',
     'input_min': 0,
     'input_max': 20,
     'cm_id': CM_ID
     },
    {'input_name': 'time resolution',
     'input_type': 'select',
     'input_parameter_name': 'time_resolution',
     'input_value': ["week", "hour", "day", "month", "year"],
     'input_unit': '',
     'input_min': '',
     'input_max': '',
     'input_priority': 1,
     'cm_id': CM_ID
     },
    # {'input_name': 'spatial resolution',
    #  'input_type': 'input',
    #  'input_parameter_name': 'spatial_resolution',
    #  'input_value': 2,
    #  'input_unit': 'km',
    #  'input_min': 1,
    #  'input_max': 10,
    #  'input_priority': 1,
    #  'cm_id': CM_ID
    #  }
]


SIGNATURE = {

    "category": "Supply",
    "cm_name": CM_NAME,
    "layers_needed": [
        "heat_tot_curr_density_tif",
    ],
    "vectors_needed": [],
    "type_layer_needed": [
      {"type": "heat", "description": "Select heat demand density layer."},
      {"type": "nuts_id_number", "description": "Hotmaps NUTS ID Number"},
        #{"type": "industrial_database_subsector", "description": "Select industrial database layer"},
    ],
     "type_vectors_needed": [
      {"type": "industrial_database_excess_heat", "description": "Select industrial site data"},
      {"type": "industrial_database_subsector", "description": "Select industrial site subsector"},
     ],
    "cm_url": "Do not add something",
    "cm_description": "CM computing the costs of the transportation of excess heat to district heating networks",
    "cm_id": CM_ID,
    "wiki_url": "https://wiki.hotmaps.eu/en/CM-Excess-heat-transport-potential",
    'inputs_calculation_module': INPUTS_CALCULATION_MODULE
}
