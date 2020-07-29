import pandas as pd
import re
import fiona
import os
import csv
import rasterio

import pandas as pd
import geopandas as gpd
from shapely.wkt import loads as loads_wkt

from pyproj import Proj, Transformer
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.wkb import loads
from skimage import measure
import numpy as np
import json as json_lib
from scipy.stats import mode


def ad_nuts_id():
    path = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(path, "data")
    path = os.path.join(path, "data_nuts_id_number.csv")
    with open(path, 'r', encoding='utf-8') as csv_file:
        delimiter = csv.Sniffer().sniff(csv_file.readline()).delimiter

    data = pd.read_csv(path, sep=delimiter)
    return data


def ad_tuw23v2(dh_areas, hdm, nuts_id):
    dh_areas = rasterio.open(dh_areas)
    dh_areas = dh_areas.read()[0]
    hdm = rasterio.open(hdm)
    root_coordinate = hdm.profile["transform"][2], hdm.profile["transform"][5]
    hdm = hdm.read()[0]
    nuts_id_raster = rasterio.open(nuts_id)
    nuts_id_raster = nuts_id_raster.read()[0]
    nuts_id_map = ad_nuts_id()

    all_labels, labels = measure.label(dh_areas, return_num=True)

    distance = 20
    in_proj = Proj(init='epsg:3035')
    out_proj = Proj(init='epsg:4326')
    transformer = Transformer.from_proj(in_proj, out_proj)
    data = []
    for label in range(labels):
        ind = all_labels == label
        xs, ys = np.where(ind != 0)
        min_xs = min(xs)
        max_xs = max(xs)
        min_ys = min(ys)
        max_ys = max(ys)
        dh_area = all_labels * ind
        nuts_id_m = nuts_id_raster * ind
        dh_area = dh_area[min_xs:max_xs + 1, min_ys:max_ys + 1].astype(bool)
        nuts_id_m = nuts_id_m[min_xs:max_xs + 1, min_ys:max_ys + 1]
        nuts_id_m = nuts_id_m.flatten()
        nuts = np.unique(nuts_id_m, return_counts=True)[0]
        if len(nuts) > 1:
            if nuts[0] == 0:
                nuts = nuts[1]
            else:
                nuts = nuts[0]
        else:
            nuts = nuts[0]
        nuts2_id = nuts_id_map[nuts_id_map["id"] == nuts].values[0][1][0:4]
        heat_demand = np.sum(dh_area * hdm[min_xs:max_xs + 1, min_ys:max_ys + 1])
        entry_point_line = np.arange(np.shape(dh_area)[1])
        entry_point_line = np.remainder(entry_point_line, distance)
        entry_point_line = np.where(entry_point_line == 0, 1, 0)
        blank_line = np.zeros(np.shape(dh_area)[1])
        entry_points = []
        for row in range(np.shape(dh_area)[0]):
            if row % distance == 0:
                entry_points.append(entry_point_line)
            else:
                entry_points.append(blank_line)
        entry_points = np.array(entry_points)
        entry_points = entry_points * dh_area
        entry_point_position = np.where(entry_points == 1)
        entry_points_coordinates = list(zip(entry_point_position[0], entry_point_position[1]))
        if len(entry_points_coordinates) == 0:
            entry_points_coordinates.append(((max_xs - min_xs) / 2, (max_ys - min_ys) / 2))
        for coordinate in entry_points_coordinates:
            lon = root_coordinate[0] + (coordinate[1] + min_ys) * 100
            lat = root_coordinate[1] - (coordinate[0] + min_xs) * 100
            lon, lat = transformer.transform(lon, lat)
            data.append([lon, lat, heat_demand / len(entry_points_coordinates), label, nuts2_id])

    data = pd.DataFrame(data, columns=["Lon", "Lat", "Heat_demand", "id", "Nuts2_ID"])

    data["ellipsoid"] = "SRID=4326"
    data["Economic_Activity"] = "Steam and air conditioning supply"
    data["Temperature"] = 100
    return data


def extract_coordinates_from_wkb_point(point):
    """
    Function extracting the coordinates from a well known byte hexadecimal string.

    :param point: Well known byte hexadecimal string describing a point.
    :type point: string
    :return: x and y coordinate of point.
    :rtype: touple of floats.
    """
    geometry = loads(point, hex=True)
    return geometry.x, geometry.y


def ad_industrial_database_dict(dictionary_heat, dictionary_subsector):
    country_to_nuts0 = {"Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Cyprus": "CY", "Czech Republic": "CZ",
                        "Germany": "DE", "Denmark": "DK", "Estonia": "EE", "Finland": "FI", "France": "FR",
                        "Greece": "EL", "Hungary": "HU", "Croatia": "HR", "Ireland": "IE", "Italy": "IT",
                        "Lithuania": "LT", "Luxembourg": "LU", "Latvia": "LV", "Malta": "MT", "Netherland": "NL",
                        "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Spain": "ES", "Sweden": "SE",
                        "Slovenia": "SI", "Slovakia": "SK", "United Kingdom": "UK", "Albania": "AL", "Montenegro": "ME",
                        "North Macedonia": "MK", "Serbia": "RS", "Turkey": "TR", "Switzerland": "CH", "Iceland": "IS",
                        "Liechtenstein": "LI", "Norway": "NO"}
    temp = '%s' % dictionary_heat
    dictionary_heat = temp.replace("\'", "\"")
    raw_data = pd.read_json(dictionary_heat, orient='records')
    raw_data = raw_data.loc[:, ("id", "geometry_wkt",  "country", "excess_heat_100_200c", "excess_heat_200_500c",
                                "excess_heat_500c")]

    raw_data["Lon"] = ""
    raw_data["Lat"] = ""
    raw_data["Nuts0"] = ""
    for i, site in raw_data.iterrows():
        # check if site location is available
        if not pd.isna(site["geometry_wkt"]) and site["geometry_wkt"] != "":
            lon, lat = re.findall(r"[-+]?\d*\.\d+|\d+", site["geometry_wkt"])
            raw_data.loc[i, "Lon"] = float(lon)
            raw_data.loc[i, "Lat"] = float(lat)
        if not pd.isna(site["country"]) and site["country"] != "":
            raw_data.loc[i, "Nuts0"] = country_to_nuts0[site["country"]]

    temp = '%s' % dictionary_subsector
    dictionary_subsector = temp.replace("\'", "\"")
    raw_data2 = pd.read_json(dictionary_subsector, orient='records')
    raw_data2 = raw_data2.loc[:, ("id", "subsector")]
    raw_data = pd.merge(raw_data, raw_data2, left_on='id', right_on='id')

    raw_data = raw_data[raw_data.Lon != ""]
    raw_data = raw_data[raw_data.Lat != ""]

    data = pd.DataFrame(columns=("Lon", "Lat", "Nuts0_ID", "Subsector", "Excess_heat", "Temperature"))
    raw_data["excess_heat_100_200c"] = pd.to_numeric(raw_data["excess_heat_100_200c"])
    raw_data["excess_heat_200_500c"] = pd.to_numeric(raw_data["excess_heat_200_500c"])
    raw_data["excess_heat_500c"] = pd.to_numeric(raw_data["excess_heat_500c"])

    for i, site in raw_data.iterrows():
        # check if heat at specific temperature range is available
        if not pd.isna(site["excess_heat_100_200c"]) and site["excess_heat_100_200c"] != "" and\
                site["excess_heat_100_200c"] != 0:
            data.loc[data.shape[0]] = (site["Lon"], site["Lat"], site["Nuts0"], site["subsector"],
                                       1000*site["excess_heat_100_200c"], 150)
        if not pd.isna(site["excess_heat_200_500c"]) and site["excess_heat_200_500c"] != "" and \
                site["excess_heat_200_500c"] != 0:
            data.loc[data.shape[0]] = (site["Lon"], site["Lat"], site["Nuts0"],
                                       site["subsector"], 1000*site["excess_heat_200_500c"], 350)
        if not pd.isna(site["excess_heat_500c"]) and site["excess_heat_500c"] != "" and site["excess_heat_500c"] != 0:
            data.loc[data.shape[0]] = (site["Lon"], site["Lat"], site["Nuts0"],
                                       site["subsector"], 1000*site["excess_heat_500c"], 500)

    return data


def ad_tuw23(out_shp_label, nuts2_id, spatial_resolution):
    """
    Function extracting potential heat sinks computed by the TUW23 CM. It creates a grid of points of constant density
    inside coherent areas.

    :param out_shp_label: File name of shp file containing the coherent areas of TUW23 CM.
    :type out_shp_label: sting
    :param nuts2_id: nuts2 id that is assigned to the points.
    :type nuts2_id: string
    :param spatial_resolution: distance between points generated in km.
    :type spatial_resolution: float
    :return: Dataframe containing the potential heat sinks and a correspondence id for each coherent aera.
    :rtype: pandas Dataframe
    """
    try:
        coherent_areas = fiona.open(out_shp_label)
    except IOError:
        return -1
    in_proj = Proj(init='epsg:3035')
    out_proj = Proj(init='epsg:4326')
    transformer = Transformer.from_proj(in_proj, out_proj)

    coherent_areas_transformed = []
    for coherent_area in coherent_areas:
        coordinates = []
        if coherent_area["geometry"]["type"] == "Polygon":
            for coordinate in coherent_area["geometry"]["coordinates"][0]:
                coordinates.append(transformer.transform(*coordinate))
            poly = Polygon(coordinates)
            poly.heat_dem = 1000*float(re.findall(r"\d+\.\d+", coherent_area["properties"]["Potential"])[0])
            coherent_areas_transformed.append(poly)
        elif coherent_area["geometry"]["type"] == "MultiPolygon":
            multipolygon_polygons = []
            for polygon in coherent_area["geometry"]["coordinates"][0]:
                coordinates = []
                for coordinate in polygon:
                    coordinates.append(transformer.transform(*coordinate))
                multipolygon_polygons.append(Polygon(coordinates))
            multi_poly = MultiPolygon(multipolygon_polygons)
            multi_poly.heat_dem = 1000*float(re.findall(r"\d+\.\d+", coherent_area["properties"]["Potential"])[0])
            coherent_areas_transformed.append(multi_poly)

    data = []
    delta = spatial_resolution / 6371 / 2 / np.pi * 360
    for i, coherent_area in enumerate(coherent_areas_transformed):
        entry_points = []
        (minx, miny, maxx, maxy) = coherent_area.bounds
        possible_x = np.arange(minx, maxx, delta)
        possible_y = np.arange(miny, maxy, delta)
        for x in possible_x:
            for y in possible_y:
                if coherent_area.buffer(0).contains(Point(x, y)):
                    entry_points.append((x, y))
        if len(entry_points) == 0:
            entry_points.append(((maxx + minx) / 2, (maxy + miny) / 2))
        induvidual_heat_demand = coherent_area.heat_dem / len(entry_points)
        for entry_point in entry_points:
            data.append([*entry_point, induvidual_heat_demand, i])

    data = pd.DataFrame(data, columns=["Lon", "Lat", "Heat_demand", "id"])
    data["Nuts2_ID"] = nuts2_id

    data["ellipsoid"] = "SRID=4326"
    data["Economic_Activity"] = "Steam and air conditioning supply"
    data["Temperature"] = 100

    return data


def ad_industry_profiles_dict(dicts):
    """
    data = []
    for dictionary in dicts:
        with open(dictionary, 'r') as file:
            raw_data = json_lib.load(file)
        raw_data = pd.DataFrame(raw_data)
        raw_data = raw_data.loc[:, ("nuts0_code", "process", "hour", "load")]
        raw_data.rename(columns={"nuts0_code": "NUTS0_code"}, inplace=True)
        raw_data["load"] = pd.to_numeric(raw_data["load"])
        raw_data["hour"] = pd.to_numeric(raw_data["hour"])
        data.append(raw_data)"""
    data = []
    for dictionary in dicts:
        temp = '%s' % dictionary
        dictionary = temp.replace("\'", "\"")
        raw_data = pd.read_json(dictionary, orient='records')
        raw_data = raw_data.loc[:, ("nuts0_code", "process", "hour", "load")]
        raw_data.rename(columns={"nuts0_code": "NUTS0_code"}, inplace=True)
        raw_data["load"] = pd.to_numeric(raw_data["load"])
        raw_data["hour"] = pd.to_numeric(raw_data["hour"])
        data.append(raw_data)

    return data


def ad_residential_heating_profile_dict(dictionary):
    """
    with open(dictionary, 'r') as file:
            data = json_lib.load(file)
    data = pd.DataFrame(data)
    data = data.loc[:, ("nuts2_code", "process", "hour", "load")]
    data.rename(columns={"nuts2_code": "NUTS2_code"}, inplace=True)
    data["load"] = pd.to_numeric(data["load"])
    data["hour"] = pd.to_numeric(data["hour"])

    """
    temp = '%s' % dictionary
    dictionary = temp.replace("\'", "\"")
    data = pd.read_json(dictionary, orient='records')
    data = data.loc[:, ("nuts2_code", "process", "hour", "load")]
    data.rename(columns={"nuts2_code": "NUTS2_code"}, inplace=True)
    data["load"] = pd.to_numeric(data["load"])
    data["hour"] = pd.to_numeric(data["hour"])

    return data


def ad_industry_profiles_local(nuts0_ids):
    """
    Loads industry profiles of different subcategories from different csv files.

    :return: List of dataframes containing the csv files data.
    :rtype: list [pd.Dataframe, pd.Dataframe, ...].
    """

    folder_names = ("hotmaps_task_2.7_load_profile_industry_chemicals_and_petrochemicals_yearlong_2018",
                    "hotmaps_task_2.7_load_profile_industry_food_and_tobacco_yearlong_2018",
                    "hotmaps_task_2.7_load_profile_industry_iron_and_steel_yearlong_2018",
                    "hotmaps_task_2.7_load_profile_industry_non_metalic_minerals_yearlong_2018",
                    "hotmaps_task_2.7_load_profile_industry_paper_yearlong_2018")

    path = os.path.dirname(
           os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(path, "data")

    data = []
    for folder_name in folder_names:
        sub_path = os.path.join(path, folder_name)
        raw_data = []
        for nuts_id in set(nuts0_ids):

            try:
                # determine delimiter of csv file
                with open(os.path.join(sub_path, str(nuts_id) + ".csv"), 'r', encoding='utf-8') as csv_file:
                    delimiter = csv.Sniffer().sniff(csv_file.readline()).delimiter
                    df = pd.read_csv(os.path.join(sub_path, str(nuts_id) + ".csv"), sep=delimiter,
                                     usecols=("NUTS0_code", "process", "hour", "load"))
                    raw_data.append(df)
            except IOError:
                pass

        if len(raw_data) > 0:
            raw_data = pd.concat(raw_data, ignore_index=True)
        else:
            raw_data = pd.DataFrame([], columns=["NUTS0_code", "process", "hour", "load"])

        data.append(raw_data)

    return data


def ad_residential_heating_profile_local(nuts2_ids):
    """
    Loads residential heating profiles from csv file.

    :return: Dataframe containing the data of the csv file.
    :rtype: pandas dataframe.
    """

    path = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(path, "data")
    path = os.path.join(path, "data_hotmaps_task_2.7_load_profile_residential_shw_and_heating_yearlong_2010")

    data = []
    for nuts_id in set(nuts2_ids):
        try:
            # determine delimiter of csv file
            with open(os.path.join(path, str(nuts_id) + ".csv"), 'r', encoding='utf-8') as csv_file:
                delimiter = csv.Sniffer().sniff(csv_file.readline()).delimiter
                df = pd.read_csv(os.path.join(path, str(nuts_id) + ".csv"), sep=delimiter,
                                 usecols=("NUTS2_code", "process", "hour", "load"))
                data.append(df)
        except IOError:
            pass

    if len(data) > 0:
        data = pd.concat(data, ignore_index=True)
    else:
        data = pd.DataFrame([], columns=["NUTS2_code", "process", "hour", "load"])

    return data


def join_point_to_nuts2(industrial_database_excess_heat, path_nuts, delimiter=','):
    gdf_nuts = gpd.read_file(path_nuts)
    df_industry = pd.read_csv(industrial_database_excess_heat, sep=delimiter, encoding='latin1')
    df_industry = df_industry.dropna(subset=['geometry_wkt'])
    #df_industry [['SRID','LATLONG']] = df_industry.geom.str.split(";", expand=True,)
    gdf_industry = gpd.GeoDataFrame( df_industry, geometry=[loads_wkt(x) for x in df_industry['geometry_wkt']], crs='EPSG:4326')
    gdf = gpd.sjoin(gdf_nuts, gdf_industry, how='right', op='intersects', lsuffix='left', rsuffix='right')
    return gdf


def ad_industrial_database_local(industrial_database_excess_heat, nuts2_ids): # here we need to get the industry sites
    """
    loads data of heat sources given by a csv file.

    :return: dataframe containing the data of the csv file.
    :rtype: pandas dataframe.
    """

    country_to_nuts0 = {"Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Cyprus": "CY", "Czech Republic": "CZ",
                        "Germany": "DE", "Denmark": "DK", "Estonia": "EE", "Finland": "FI", "France": "FR",
                        "Greece": "EL", "Hungary": "HU", "Croatia": "HR", "Ireland": "IE", "Italy": "IT",
                        "Lithuania": "LT", "Luxembourg": "LU", "Latvia": "LV", "Malta": "MT", "Netherland": "NL",
                        "Netherlands": "Nl",
                        "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Spain": "ES", "Sweden": "SE",
                        "Slovenia": "SI", "Slovakia": "SK", "United Kingdom": "UK", "Albania": "AL", "Montenegro": "ME",
                        "North Macedonia": "MK", "Serbia": "RS", "Turkey": "TR", "Switzerland": "CH", "Iceland": "IS",
                        "Liechtenstein": "LI", "Norway": "NO"}
    path = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    print(path)
    #path_industry = os.path.join(os.path.join(path, "data"), "Industrial_Database.csv")
    path_nuts = os.path.join(os.path.join(path, "data"), "Nuts2_4326.geojson")
    print("#"*20,"path_nuts")
    print(path)
    print(path_nuts)
    # determine delimiter of csv file
    #with open(path_industry, 'r', encoding='utf-8') as csv_file:
    #    delimiter = csv.Sniffer().sniff(csv_file.readline()).delimiter

    #raw_data = pd.read_csv(path_industry, sep=delimiter, usecols=("geom", "Subsector", "Excess_Heat_100-200C",
    #                                                     "Excess_Heat_200-500C", "Excess_Heat_500C",
    #                                                     "Country")) #, "Nuts2_ID"

    gdf = join_point_to_nuts2(industrial_database_excess_heat, path_nuts)
    #print (gdf)
    raw_data = pd.DataFrame(gdf)
    raw_data.rename(columns={'NUTS2_ID': 'Nuts2_ID'}, inplace=True)
    #print(raw_data)

    Subsector = "Iron and steel"

    raw_data = raw_data[raw_data["Nuts2_ID"].isin(nuts2_ids)]
    # dataframe for processed data
    data = pd.DataFrame(columns=("ellipsoid", "Lon", "Lat", "Nuts0_ID", "Subsector", "Excess_heat", "Temperature",
                                 "Nuts2_ID"))

    for i, site in raw_data.iterrows():
        # check if site location is available
        if not pd.isna(site["geometry_wkt"]):
            # extract ellipsoid model and (lon, lat) from the "geom" column
            #ellipsoid, coordinate = site["geometry_wkt"].split(";")
            ellipsoid = site['srid']
            coordinate = site['geometry_wkt']

            m = re.search(r"[-+]?[0-9]*\.?[0-9]+.[-+]?[0-9]*\.?[0-9]+", coordinate)
            m = m.group(0)
            lon, lat = m.split(" ")
            lon = float(lon)
            lat = float(lat)

            nuts0 = country_to_nuts0[site["country"]]

            if "Subsector" in site.index:
                # check if heat at specific temperature range is available
                # TODO deal with units; hard coded temp ranges?
                if not pd.isna(site["excess_heat_100_200c"]) and site["excess_heat_100_200c"] != 0:
                    data.loc[data.shape[0]] = (ellipsoid, lon, lat, nuts0, site["subsector"],
                                               site["excess_heat_100_200c"] * 1000, 150, site["Nuts2_ID"])
                if not pd.isna(site["excess_heat_200_500c"]) and site["excess_heat_200_500c"] != 0:
                    data.loc[data.shape[0]] = (ellipsoid, lon, lat, nuts0,
                                               site["Subsector"], site["excess_heat_200_500c"] * 1000, 350,
                                               site["Nuts2_ID"])
                if not pd.isna(site["excess_heat_500c"]) and site["excess_heat_500c"] != "" and\
                        site["excess_heat_500c"] != 0:
                    data.loc[data.shape[0]] = (ellipsoid, lon, lat, nuts0,
                                               site["Subsector"], site["excess_heat_500c"] * 1000, 500, site["Nuts2_ID"])
            else:
                # check if heat at specific temperature range is available
                # TODO deal with units; hard coded temp ranges?
                if not pd.isna(site["excess_heat_100_200c"]) and site["excess_heat_100_200c"] != 0:
                    data.loc[data.shape[0]] = (ellipsoid, lon, lat, nuts0, "Iron and steel",
                                               site["excess_heat_100_200c"] * 1000, 150, site["Nuts2_ID"])
                if not pd.isna(site["excess_heat_200_500c"]) and site["excess_heat_200_500c"] != 0:
                    data.loc[data.shape[0]] = (ellipsoid, lon, lat, nuts0,
                                               "Iron and steel", site["excess_heat_200_500c"] * 1000, 350,
                                               site["Nuts2_ID"])
                if not pd.isna(site["excess_heat_500c"]) and site["excess_heat_500c"] != "" and \
                        site["excess_heat_500c"] != 0:
                    data.loc[data.shape[0]] = (ellipsoid, lon, lat, nuts0,
                                               "Iron and steel", site["excess_heat_500c"] * 1000, 500,
                                               site["Nuts2_ID"])

    data["id"] = range(data.shape[0])

    return data

#if __name__ == "__main__":
#    path = os.path.dirname(
#        os.path.dirname(os.path.abspath(__file__)))
#
#    path_industry = os.path.join(os.path.join(path, "data"), "Industrial_Database.csv")
#    path_nuts = os.path.join(os.path.join(path, "data"), "Nuts2_4326.shp")
#
#    with open(path_industry, 'r', encoding='utf-8') as csv_file:
#        delimiter = csv.Sniffer().sniff(csv_file.readline()).delimiter
#
#    raw_data = pd.read_csv(path_industry, sep=delimiter, usecols=("geom", "Subsector", "Excess_Heat_100-200C",
#                                                         "Excess_Heat_200-500C", "Excess_Heat_500C",
#                                                         "Country", "Nuts2_ID"))
#    delimiter =";"
#    gdf = join_point_to_nuts2(path_industry, path_nuts, delimiter)
#    print(gdf)
#    raw_data = pd.DataFrame(gdf)
#    raw_data.rename(columns={'NUTS2_ID': 'Nuts2_ID'}, inplace=True)
#    raw_data.to_csv('OUT.csv')