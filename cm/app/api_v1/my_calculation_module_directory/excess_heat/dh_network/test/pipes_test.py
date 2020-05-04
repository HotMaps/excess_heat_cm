import unittest
import numpy as np
from dh_network.dh_objects import TransmissionLine
import parameters as p


class TestNetworkGraph(unittest.TestCase):

    def test_initiation(self):
        transmission_line = TransmissionLine()
        self.assertIsInstance(transmission_line, TransmissionLine)

    def test_investment(self):
        transmission_line = TransmissionLine()
        transmission_line.length = 10
        self.assertAlmostEqual(transmission_line.length * p.PIPE_COSTS[0], transmission_line.investment(), 3)

    def test_annuity(self):
        transmission_line = TransmissionLine()
        transmission_line.length = 10
        self.assertAlmostEqual(99.48755567449248, transmission_line.annuity())

    def test_heat_loss(self):
        transmission_line = TransmissionLine()
        transmission_line.length = 10
        self.assertAlmostEqual(8640.627038241379, transmission_line.heat_loss())

    def test_pump_energy_cost(self):
        transmission_line = TransmissionLine()
        transmission_line.length = 10
        transmission_line.flow = np.abs(np.sin(np.linspace(0, 8760, num=8760)))
        self.assertAlmostEqual(50047.51965272181, transmission_line.pump_energy_cost())

    def test_specific_costs(self):
        transmission_line = TransmissionLine()
        transmission_line.length = 10
        transmission_line.flow = np.abs(np.sin(np.linspace(0, 8760, num=8760)))
        self.assertAlmostEqual(np.inf, transmission_line.specific_costs())

        transmission_line = TransmissionLine()
        transmission_line.length = 0.1
        transmission_line.flow = np.abs(np.sin(np.linspace(0, 8760, num=8760)))
        self.assertAlmostEqual(0.09137348865763197, transmission_line.specific_costs())

    def test_find_lowest_specific_costs(self):
        transmission_line = TransmissionLine()
        transmission_line.length = 0.1
        transmission_line.flow = np.abs(np.sin(np.linspace(0, 8760, num=8760)))
        transmission_line.find_lowest_specific_costs()
        self.assertEqual(7, transmission_line.selection)

        transmission_line.length = 1
        transmission_line.find_lowest_specific_costs()
        self.assertEqual(7, transmission_line.selection)

    def test_find_recommended_selection(self):
        transmission_line = TransmissionLine()
        transmission_line.length = 0.1
        transmission_line.flow = np.abs(np.sin(np.linspace(0, 8760, num=8760)))
        transmission_line.find_recommended_selection()
        self.assertEqual(3, transmission_line.selection)

