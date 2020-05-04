import operator
from geopy.distance import distance
import numpy as np


def temp_check(temp_source, temp_sink, condition):
    """
    function determining if source can provide heat for a sink.

    :param temp_source: temperature of the heat source.
    :type temp_source: float.
    :param temp_sink: temperature of the heat sink.
    :type temp_sink: float.
    :param condition: determines condition the temperature check uses.
    :type condition: str of following list [">", ">=", "=", "<", "<=", "!=", "true", "false"].

    :return: returns true, if source can provide heat for sink.
    :rtype: bool.
    """
    operators = {">": operator.gt, ">=": operator.ge, "=": operator.eq, "<": operator.lt, "<=": operator.le,
                 "!=": operator.ne}

    if condition in operators.keys():
        if operators[condition](temp_source, temp_sink):
            return True
    elif condition == "true":
        return True
    elif condition == "false:":
        return False


def orthodrome_distance(coordinate_1, coordinate_2, ellipsoid="WGS-84"):
    """
    function computing the geodesic distance of two points on an ellipsoid (aka orthodrome).

    :param coordinate_1: (longitude, latitude) of first location.
    :type coordinate_1: tuple(float, float).
    :param coordinate_2: (longitude, latitude) of second location.
    :type coordinate_2: tuple(float, float).
    :param ellipsoid: optional ellipsoid model used for computation of distance.
    :type ellipsoid: str {"WGS-84", "GRS_80", "Airy (1830)", "Intl 1924", "Clarke (1880)", "GRS-67"}.

    :return: orthodrome length in m.
    :rtype: float.
    """

    return distance(coordinate_1, coordinate_2, ellipsoid=ellipsoid).m


def approximate_distance(coordinate_1, coordinate_2):
    """
    function computing the approximate distance of two points  with small angle approximation.

    :param coordinate_1: (longitude, latitude) of first location.
    :type coordinate_1: tuple(float, float).
    :param coordinate_2: (longitude, latitude) of second location.
    :type coordinate_2: tuple(float, float).

    :return: distance in m.
    :rtype: float.
    """

    return ((coordinate_2[0] - coordinate_1[0]) ** 2 + (coordinate_2[1] - coordinate_1[1]) ** 2)**0.5 /\
        360 * 6378137 * 2 * np.pi


def find_neighbours(sites1, sites2, max_distance, network_temp=100, site1_condition="true", site2_condition="true",
                    site1_site2_condition="true", small_angle_approximation=True):
    """
    Function searching for neighbours in a fixed search radius. Only adds the next neighbour if all temperature
    conditions are met.

    :param sites1: Dataframe containing coordinates of sites 1.
    :type sites1: pandas Dataframe
    :param sites2: Dataframe containing coordinates of sites 2.
    :type sites2: pandas Dataframe
    :param max_distance: Maximum distance in km for the fixed radius search.
    :type max_distance: float
    :param network_temp: Temperature of the network in °C. The site1_condition and site2_condition are in reference to
                         this network temperature.
    :type network_temp: float
    :param site1_condition: Condition the site 1 temp should fulfill in aspect to the network temp.
    :type site1_condition: str of following list [">", ">=", "=", "<", "<=", "!=", "true", "false"]
    :param site2_condition: Condition the site 2 temp should fulfill in aspect to the network temp.
    :type site2_condition: str of following list [">", ">=", "=", "<", "<=", "!=", "true", "false"]
    :param site1_site2_condition: Condition the site 1 temp should fulfill in aspect the the site 2 temp.
    :type site1_site2_condition: str of following list [">", ">=", "=", "<", "<=", "!=", "true", "false"]
    :param small_angle_approximation: Determines if small angle approximation should be used for the distance
                                      calculation.
    :type small_angle_approximation: bool
    :return: Adjacency list and distances.
    :rtype: tuple of Adjacency list and distances. Both lists have the same shape.
    """
    # get indices of columns
    lon1_ind = sites1.columns.get_loc("Lon")
    lat1_ind = sites1.columns.get_loc("Lat")
    lon2_ind = sites2.columns.get_loc("Lon")
    lat2_ind = sites2.columns.get_loc("Lat")
    temp1_ind = sites1.columns.get_loc("Temperature")
    temp2_ind = sites2.columns.get_loc("Temperature")

    connections = []
    distances = []
    for site1 in sites1.values:
        connections.append([])
        distances.append([])
        coordinate1 = (site1[lon1_ind], site1[lat1_ind])
        temp1 = site1[temp1_ind]
        for i, site2 in enumerate(sites2.values):
            coordinate2 = (site2[lon2_ind], site2[lat2_ind])
            temp2 = site2[temp2_ind]
            # check if source and sink are close enough
            if small_angle_approximation is False:
                dist = orthodrome_distance(coordinate1, coordinate2)
            else:
                dist = approximate_distance(coordinate1, coordinate2)
            if dist <= max_distance:
                if temp_check(temp1, network_temp, site1_condition) and \
                        temp_check(temp2, network_temp, site2_condition) and \
                        temp_check(temp1, temp2, site1_site2_condition):
                    connections[-1].append(i)
                    distances[-1].append(dist)

    return connections, distances


def annuity_costs(cost, discount_rate, years):
    if discount_rate == 0:
        return cost / years
    else:
        return cost * (discount_rate + 1) ** years * discount_rate / ((discount_rate + 1) ** years - 1)


def moving_average(array, order):
    """
    returns the moving average of the specified order.

    :param array: array of which the moving average should be computed.
    :type array: array like.
    :param order: order of moving average.
    :type order: int.
    :return: moving average of array.
    :rtype: array of same length as the input array.
    """
    return np.convolve(array, [1] * order) / order


def transpose4with1(array):
    template = [[[[] for _ in subsub] for subsub in subarray] for subarray in array[0]]
    for subarray in array:
        for i, subsub in enumerate(subarray):
            for j, subsubsub in enumerate(subsub):
                for k, value in enumerate(subsubsub):
                    template[i][j][k].append(value)
    return template


def create_normalized_profiles(profiles, region_header, time_header, value_header):
    """
    function normalizing profiles so that the sum of values over all time stamps of each region is 1

    :param profiles: dataframe containing profiles of different regions.
    :type profiles: pandas dataframe.
    :param region_header: header indicating the column containing the names of the regions.
    :type region_header: str.
    :param time_header: header indicating the column containing the time stamps of the profiles.
    :type time_header: str.
    :param value_header: header indicating the column containing the value of the profile.
    :type value_header: str.
    :return: list containing normalized profiles in form of numpy arrays. The keys are the region names.
    :rtype: dictionary {region_name: np.array(profile), region_name2: np.array(profile2), ...}
    """

    normalized_profiles = dict()
    regions = profiles[region_header].unique()
    for region in regions:
        profile = profiles.loc[profiles[region_header] == region]
        profile = profile.sort_values(time_header)
        profile = np.array(profile[value_header].values)
        profile = profile / np.sum(profile)
        normalized_profiles[region] = profile
    return normalized_profiles


def round_to_n(x, n):
    length = 0
    if x > 1:
        while x > 1:
            x /= 10
            length += 1
    elif x == 0:
        return 0
    else:
        while x < 1:
            x *= 10
            length -= 1

    return round(x, n) * 10 ** length
