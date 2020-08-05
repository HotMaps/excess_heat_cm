from scipy.stats import percentileofscore
from ..utility import annuity_costs, moving_average
from ..parameters import *


class NetworkObject:
    def __init__(self, time_unit=list(TIME_RESOLUTION_MAP.keys())[0], lifetime=30, discount_rate=0.03,
                 operational_costs_factor=0.01):
        self.flow = []
        self.time_unit = time_unit
        self.lifetime = lifetime
        self.discount_rate = discount_rate
        self.operational_costs_factor = operational_costs_factor

    def investment(self):
        raise NotImplementedError()

    def annuity(self):
        return annuity_costs(self.investment(), self.discount_rate, self.lifetime)

    def operational_costs(self):
        return self.investment() * self.operational_costs_factor

    def annual_costs(self):
        return self.annuity() + self.operational_costs()

    def specific_costs(self):
        transported_heat = np.sum(self.flow)
        if transported_heat > 0:
            return self.annual_costs() / transported_heat
        else:
            return 1e12


class TransmissionLine(NetworkObject):
    def __init__(self, country=list(ELECTRICITY_PRICE_MAP.keys())[0], time_unit=list(TIME_RESOLUTION_MAP.keys())[0],
                 lifetime=30, discount_rate=0.03, liquid_temperature=100, length=0, operational_costs_factor=0.01):
        super().__init__(time_unit=time_unit, lifetime=lifetime, discount_rate=discount_rate,
                         operational_costs_factor=operational_costs_factor)

        self.power_to_pressure_drop = (np.array(PRESSURE_DROP) / np.array(PIPE_CAPACITIES_AT_OPTIMUM) ** 2).tolist()
        self.power_to_flow_vel = (np.array(OPTIMAL_FLOW_VELOCITY) / np.array(PIPE_CAPACITIES_AT_OPTIMUM)).tolist()
        self.selection = 0
        self.length = length
        self.liquid_temperature = liquid_temperature
        self.country = country

    def investment(self):
        return self.length * PIPE_COSTS[self.selection]

    def heat_loss(self):
        delta_t = self.liquid_temperature - SOIL_TEMPERATURE_MAP[self.country]
        return np.pi * INSULATOR_CONDUCTIVITY * delta_t * 10e-6 * self.length / \
            np.log(1 + 2 * INSULATOR_THICKNESS[self.selection] / PIPE_DIAMETER[self.selection]) * 8760

    def pump_energy_cost(self):
        energy = 0
        for f in moving_average(self.flow, CONVOLUTION_MAP[self.time_unit]):
            power = f / TIME_RESOLUTION_MAP[self.time_unit]
            pressure_drop = power ** 2 * self.power_to_pressure_drop[self.selection] * self.length
            cross_section = np.pi * (PIPE_HYDRAULIC_DIAMETER[self.selection] / 2000)**2
            volumetric_flow_rate = power * self.power_to_flow_vel[self.selection] * cross_section

            energy += pressure_drop * volumetric_flow_rate / HYDROMECHANICAL_PUMP_EFFICIENCY
        energy *= TIME_RESOLUTION_MAP[self.time_unit] / 3.6e6   # convert to kWh per year
        costs = energy * ELECTRICITY_PRICE_MAP[self.country] / 1e2
        return costs

    def annual_costs(self):
        return self.annuity() + self.operational_costs() + self.pump_energy_cost()

    def specific_costs(self):
        transported_heat = np.sum(self.flow) - self.heat_loss()
        if transported_heat > 0:
            return self.annual_costs() / transported_heat
        else:
            return 1e12

    def find_lowest_specific_costs(self):
        lowest_selection = 0
        lowest_specific_costs = 1e12
        for i in range(len(PIPE_COSTS)):
            self.selection = i
            specific_costs = self.specific_costs()
            if specific_costs < lowest_specific_costs:
                lowest_specific_costs = specific_costs
                lowest_selection = i
        self.selection = lowest_selection

    def find_recommended_selection(self):
        f = moving_average(self.flow, CONVOLUTION_MAP[self.time_unit]) / TIME_RESOLUTION_MAP[self.time_unit]
        i = 0
        while percentileofscore(f, PIPE_CAPACITIES_AT_OPTIMUM[i]) < 90:
            i += 1

        self.selection = i


class LiquidPump(NetworkObject):
    def investment(self):
        capacity = np.max(moving_average(self.flow, CONVOLUTION_MAP[self.time_unit]))
        if capacity < 1:
            return capacity * PUMP_COST_SUB_1MW
        else:
            return capacity * PUMP_COST_ABOVE_1MW


class LiquidLiquidHeatExchanger(NetworkObject):
    def investment(self):
        capacity = np.max(moving_average(self.flow, CONVOLUTION_MAP[self.time_unit]))
        if capacity < 1:
            return capacity * LIQUID_TO_LIQUID_HEAT_EXCHANGER_COST_SUB_1MW
        else:
            return capacity * LIQUID_TO_LIQUID_HEAT_EXCHANGER_COST_ABOVE_1MW


class AirLiquidHeatExchanger(NetworkObject):
    def investment(self):
        return np.max(moving_average(self.flow, CONVOLUTION_MAP[self.time_unit])) * \
               AIR_TO_LIQUID_HEAT_EXCHANGER_COST
