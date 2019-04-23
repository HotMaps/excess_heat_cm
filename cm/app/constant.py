
CELERY_BROKER_URL_DOCKER = 'amqp://admin:mypass@rabbit:5672/'
CELERY_BROKER_URL_LOCAL = 'amqp://localhost/'



CM_REGISTER_Q = 'rpc_queue_CM_register'
CM_NAME = 'Excess heat'
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
     'input_unit': 'MWh/ha',
     'input_min': 0,
     'input_max': 1000,
     'cm_id': CM_ID
     },
    {'input_name': 'Min. heat demand in a DH area',
     'input_type': 'input',
     'input_parameter_name': 'DH_threshold',
     'input_value': 30,
     'input_unit': 'GWh/year',
     'input_min': 0,
     'input_max': 500,
     'cm_id': CM_ID
     },
    {'input_name': 'Maximum search radius',
     'input_type': 'input',
     'input_parameter_name': 'search_radius',
     'input_value': 20,
     'input_unit': 'km',
     'input_min': 0,
     'input_max': 100,
     'cm_id': CM_ID
     },
    {'input_name': 'Investment period',
     'input_type': 'input',
     'input_parameter_name': 'investment_period',
     'input_value': 20,
     'input_unit': 'year',
     'input_min': 0,
     'input_max': 50,
     'cm_id': CM_ID
     },
    {'input_name': 'Transmission line threshold',
     'input_type': 'input',
     'input_parameter_name': 'transmission_line_threshold',
     'input_value': 0.5,
     'input_unit': 'ct/kwWh',
     'input_min': 0,
     'input_max': 20,
     'cm_id': CM_ID
     }
]


SIGNATURE = {
    "category": "Buildings",
    "cm_name": CM_NAME,
    "layers_needed": [
        "heat_tot_curr_density_tif",
    ],
    "vectors_needed": [

    ],
    "type_layer_needed": [
        "heat",
    ],
    "cm_url": "Do not add something",
    "cm_description": "CM computing the costs of the transportation of excess heat to district heating networks",
    "cm_id": CM_ID,
    'inputs_calculation_module': INPUTS_CALCULATION_MODULE
}
