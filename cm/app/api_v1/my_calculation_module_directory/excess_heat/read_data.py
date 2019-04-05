import pandas as pd
import re
import fiona

from pyproj import Proj, transform
from shapely.geometry import Point, Polygon, MultiPolygon
import numpy as np

from .sql import extract_coordinates_from_wkb_point


def ad_industrial_database_dict(dict):
    country_to_nuts0 = {"Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Cyprus": "CY", "Czech Republic": "CZ",
                        "Germany": "DE", "Denmark": "DK", "Estonia": "EE", "Finland": "FI", "France": "FR",
                        "Greece": "EL", "Hungary": "HU", "Croatia": "HR", "Ireland": "IE", "Italy": "IT",
                        "Lithuania": "LT", "Luxembourg": "LU", "Latvia": "LV", "Malta": "MT", "Netherland": "Nl",
                        "Netherlands": "Nl",
                        "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Spain": "ES", "Sweden": "SE",
                        "Slovenia": "SI", "Slovakia": "SK", "United Kingdom": "UK", "Albania": "AL", "Montenegro": "ME",
                        "North Macedonia": "MK", "Serbia": "RS", "Turkey": "TR", "Switzerland": "CH", "Iceland": "IS",
                        "Liechtenstein": "LI", "Norway": "NO"}
    raw_data = pd.DataFrame(dict["industrial_database"])
    raw_data = raw_data.loc[:, ("geom", "subsector",  "country", "excess_heat_100_200c", "excess_heat_200_500c",
                                "excess_heat_500c")]
    raw_data["Lon"] = ""
    raw_data["Lat"] = ""
    raw_data["Nuts0"] = ""
    for i, site in raw_data.iterrows():
        # check if site location is available
        if not pd.isna(site["geom"]) and site["geom"] != "":
            lon, lat = extract_coordinates_from_wkb_point(site["geom"])
            raw_data.loc[i, "Lon"] = lon
            raw_data.loc[i, "Lat"] = lat
        if not pd.isna(site["country"]) and site["country"] != "":
            raw_data.loc[i, "Nuts0"] = country_to_nuts0[site["country"]]

    raw_data = raw_data[raw_data.Lon != ""]
    raw_data = raw_data[raw_data.Lat != ""]

    data = pd.DataFrame(columns=("Lon", "Lat", "Nuts0_ID", "Subsector", "Excess_heat", "Temperature"))
    raw_data["excess_heat_100_200c"] = pd.to_numeric(raw_data["excess_heat_100_200c"])
    raw_data["excess_heat_200_500c"] = pd.to_numeric(raw_data["excess_heat_200_500c"])
    raw_data["excess_heat_500c"] = pd.to_numeric(raw_data["excess_heat_500c"])


    for i, site in raw_data.iterrows():
        # check if heat at specific temperature range is available
        # TODO deal with units; hard coded temp ranges?
        if not pd.isna(site["excess_heat_100_200c"]) and site["excess_heat_100_200c"] != "" and site["excess_heat_100_200c"] != 0:
            data.loc[data.shape[0]] = (site["Lon"], site["Lat"], site["Nuts0"], site["subsector"],
                                       1000*site["excess_heat_100_200c"], 150)
        if not pd.isna(site["excess_heat_200_500c"]) and site["excess_heat_200_500c"] != "" and site["excess_heat_200_500c"] != 0:
            data.loc[data.shape[0]] = (site["Lon"], site["Lat"], site["Nuts0"],
                                       site["subsector"], 1000*site["excess_heat_200_500c"], 350)
        if not pd.isna(site["excess_heat_500c"]) and site["excess_heat_500c"] != "" and site["excess_heat_500c"] != 0:
            data.loc[data.shape[0]] = (site["Lon"], site["Lat"], site["Nuts0"],
                                       site["subsector"], 1000*site["excess_heat_500c"], 500)

    return data


def ad_TUW23(out_shp_label, nuts2_id):
    """
    Function extracting potential heat sinks computed by the TUW23 CM. It creates a grid of points of constant density
    inside coherent areas.

    :param out_shp_label: File name of shp file containing the coherent areas of TUW23 CM.
    :type out_shp_label: sting
    :return: Dataframe containing the potential heat sinks and a correspondence id for each coherent aera.
    :rtype: pandas Dataframe
    """
    coherent_areas = fiona.open(out_shp_label)
    inProj = Proj(init='epsg:3035')
    outProj = Proj(init='epsg:4326')

    coherent_areas_transformed = []
    for coherent_area in coherent_areas:
        coordinates = []
        if coherent_area["geometry"]["type"] == "Polygon":
            for coordinate in coherent_area["geometry"]["coordinates"][0]:
                coordinates.append(transform(inProj, outProj, *coordinate))
            poly = Polygon(coordinates)
            poly.heat_dem = 1000*float(re.findall("\d+\.\d+", coherent_area["properties"]["Potential"])[0])
            coherent_areas_transformed.append(poly)
        elif coherent_area["geometry"]["type"] == "MultiPolygon":
            multipolygon_polygons = []
            for polygon in coherent_area["geometry"]["coordinates"][0]:
                coordinates = []
                for coordinate in polygon:
                    coordinates.append(transform(inProj, outProj, *coordinate))
                multipolygon_polygons.append(Polygon(coordinates))
            multi_poly = MultiPolygon(multipolygon_polygons)
            multi_poly.heat_dem = 1000*float(re.findall("\d+\.\d+", coherent_area["properties"]["Potential"])[0])
            coherent_areas_transformed.append(multi_poly)

    data = []
    delta = 0.015
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
            entry_points.append((maxx, maxy))
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
    dict_names = ["load_profile_industry_chemicals_and_petrochemicals_yearlong_2018", "load_profile_industry_food_and_tobacco_yearlong_2018",
                  "load_profile_industry_iron_and_steel_yearlong_2018", "load_profile_industry_non_metalic_minerals_yearlong_2018",
                  "load_profile_industry_paper_yearlong_2018"]
    data = []
    for name, dict in zip(dict_names, dicts):
        raw_data = pd.DataFrame(dict[name])
        raw_data = raw_data.loc[:, ("NUTS0_code", "process", "hour", "load")]
        raw_data["load"] = pd.to_numeric(raw_data["load"])
        raw_data["hour"] = pd.to_numeric(raw_data["hour"])
        data.append(raw_data)

    return data


def ad_residential_heating_profile_dict(dict):

    data = pd.DataFrame(dict["load_profile_residential_heating_yearlong_2010"])
    data = data.loc[:, ("NUTS2_code", "process", "hour", "load")]
    data["load"] = pd.to_numeric(data["load"])
    data["hour"] = pd.to_numeric(data["hour"])
    return data


