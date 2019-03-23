import fiona
from fiona.crs import from_epsg
from collections import OrderedDict

output_driver = "ESRI Shapefile"
schema = {
                "geometry": "LineString",
                "properties": OrderedDict([
                    ("annual_flow", "float"),
                    ("temperature", "float")
                ])
                }


def create_transmission_line_shp(transmission_lines, flows, temperatures, file):
    with fiona.open(file,  "w", crs=from_epsg(4326), driver=output_driver, schema=schema) as shp:
        for transmission_line, flow, temperature in zip(transmission_lines, flows, temperatures):
            line = {
                "geometry": {
                    "type": "LineString",
                    "coordinates": transmission_line
                },
                "properties": OrderedDict([
                    ("annual_flow", flow),
                    ("temperature", temperature)
                ])
            }
            shp.write(line)


if __name__ == "__main__":
    transmissions = [((0,0), (1,1)), ((1,1), (2,1))]
    flows = [2, 3]
    temperatures = [100, 200]
    create_transmission_line_shp(transmissions, flows, temperatures, "./test.shp")