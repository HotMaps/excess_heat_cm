import numpy as np

# maximum continuous power in MW
PIPE_CAPACITIES_AT_OPTIMUM = [0.2, 0.3, 0.6, 1.2, 1.9, 3.6, 6.1, 9.8, 20, 45, 75, 125, 190, 380, 570, 4 * 190, 5 * 190,
                              6 * 190, 7 * 190, 8 * 190, 9 * 190, 10 * 190]
# total costs in Euro/m
PIPE_COSTS = [195, 206, 220, 240, 261, 288, 323, 357, 426, 564, 701, 839, 976, 2 * 976, 3 * 976, 4 * 976, 5 * 976,
              6 * 976, 7 * 976, 8 * 976, 9 * 976, 10 * 976]
# pipe hydraulic diameter in mm for cross section computation
PIPE_HYDRAULIC_DIAMETER = [37.2, 43.1, 54.5, 70.3, 82.5, 107.1, 132.5, 160.3, 210.1, 312.7, 393.8, 495.4, 595.8,
                           np.sqrt(2) * 595.8, np.sqrt(3) * 595.8, np.sqrt(4) * 595.8, np.sqrt(5) * 595.8,
                           np.sqrt(6) * 595.8, np.sqrt(7) * 595.8, np.sqrt(8) * 595.8, np.sqrt(9) * 595.8,
                           np.sqrt(10) * 595.8]
# pipe diameter for circumference computation
PIPE_DIAMETER = [37.2, 43.1, 54.5, 70.3, 82.5, 107.1, 132.5, 160.3, 210.1, 312.7, 393.8, 495.4, 595.8, 2 * 595.8,
                 3 * 595.8, 4 * 595.8, 5 * 595.8, 6 * 595.8, 7 * 595.8, 8 * 595.8, 9 * 595.8, 10 * 595.8]
# insulator thickness in mm
INSULATOR_THICKNESS = [60, 60, 60, 80, 80, 100, 125, 165, 175, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200,
                       200, 200, 200]
# optimal flow velocity in m/s
OPTIMAL_FLOW_VELOCITY = [0.9, 0.9, 1, 1.2, 1.3, 1.6, 1.8, 2, 2.4, 2.6, 2.7, 2.9, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
# pressure drop in pa/m at optimal flow velocity
PRESSURE_DROP = [600, 500, 420, 450, 420, 500, 480, 470, 500, 360, 345, 250, 230, 230, 230, 230, 230, 230, 230, 230,
                 230, 230]
# insulator conductivity of pipe in W/m/K
INSULATOR_CONDUCTIVITY = 0.05
# efficiency for pumping liquids
HYDROMECHANICAL_PUMP_EFFICIENCY = 0.8

# Euro / MW
AIR_TO_LIQUID_HEAT_EXCHANGER_COST = 15000
LIQUID_TO_LIQUID_HEAT_EXCHANGER_COST_SUB_1MW = 265000
LIQUID_TO_LIQUID_HEAT_EXCHANGER_COST_ABOVE_1MW = 100000
PUMP_COST_SUB_1MW = 240000
PUMP_COST_ABOVE_1MW = 90000

# mapping time settings to full hour integers, 8760 must should be dividable by it
TIME_RESOLUTION_MAP = {"hour": 1, "day": 10, "week": 146, "month": 730, "year": 8760}
# time units to average to account for thermal inertia of the system
CONVOLUTION_MAP = {"hour": 6, "day": 1, "week": 1, "month": 1, "year": 1}

# electricity price used for pumps in ct/kWh
ELECTRICITY_PRICE_MAP = {'BE': 24, 'BG': 10.8, 'CZ': 17.8, 'DK': 18.9, 'DE': 22.5, 'EE': 11.9, 'IE': 20.7,
                         'EL': 17.4, 'ES': 26.5, 'FR': 15.6, 'HR': 13.2, 'IT': 22, 'CY': 18.1, 'LV': 19, 'LT': 12.1,
                         'LU': 14.9, 'HU': 11.7, 'MT': 19.9, 'NL': 15, 'AT': 15.9, 'PL': 14.7, 'PT': 20.1,
                         'RO': 10.3, 'SI': 14.1, 'SK': 20, 'FI': 9.4, 'SE': 15.4, 'UK': 17.5}
# average annual soil temperature in degrees centigrade used for heat loss calculations
SOIL_TEMPERATURE_MAP = {'BE': 9.5, 'BG': 10.5, 'CZ': 7.5, 'DK': 7.5, 'DE': 8.5, 'EE': 5.1, 'IE': 9.3,
                        'EL': 15.4, 'ES': 13.3, 'FR': 10.7, 'HR': 10.9, 'IT': 13.4, 'CY': 18.4, 'LV': 5.6, 'LT': 6.2,
                        'LU': 8.6, 'HU': 9.7, 'MT': 19.2, 'NL': 9.2, 'AT': 6.3, 'PL': 7.8, 'PT': 15.1,
                        'RO': 8.8, 'SI': 8.9, 'SK': 6.8, 'FI': 1.7, 'SE': 2.1, 'UK': 8.4}

INDUSTRIAL_SUBSECTOR_MAP = {"Iron and steel": "iron_and_steel", "Refineries": "chemicals_and_petrochemicals",
                            "Chemical industry": "chemicals_and_petrochemicals", "Cement": "non_metalic_minerals",
                            "Glass": "non_metalic_minerals", "Non-metallic mineral products": "non_metalic_minerals",
                            "Paper and printing": "paper", "Non-ferrous metals": "iron_and_steel",
                            "Other non-classified": "food_and_tobacco"}
