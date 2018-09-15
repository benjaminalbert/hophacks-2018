import urllib.request
import json
import math
from PIL import Image
from io import BytesIO
from tkinter import Tk, StringVar, mainloop, END
from tkinter.messagebox import showinfo
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Entry, OptionMenu, Button, Label

api_key = "5xUJBVluRAAdW4HaVuQxyEbNlGHGEtjX"


class LatLon:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def distance(self, latlon):
        return math.sqrt((latlon.lat - self.lat)**2 + (latlon.lon - self.lon)**2)

    def __gt__(self, other):
        return self.lat > other.lat and self.lon > other.lon

    def __lt__(self, other):
        return self.lat < other.lat and self.lon < other.lon

    def __repr__(self):
        return "{},{}".format(self.lat, self.lon)


class Route:
    def __init__(self, latlons, narratives):
        self.latlons = latlons
        self.narratives = narratives
        self.crime_score = 0


class Crime:
    def __init__(self, latlon, severity):
        self.latlon = latlon
        self.severity = severity


class VectorCrimeMap:
    def __init__(self, crimes):
        self.crimes = crimes

    def score_location(self, latlon, crime_neighborhood_percentage=0.01):
        if not self.crimes or len(self.crimes) == 0:
            raise Exception("cannot score location safety with empty crime list")
        total_crimes_to_factor = len(self.crimes) * crime_neighborhood_percentage
        if total_crimes_to_factor <= 0:
            total_crimes_to_factor = 1
        nearest_crimes = sorted(self.crimes, key=lambda crime: crime.latlon.distance(latlon), reverse=True)
        crime_score = 0
        crime_index = 0
        while crime_index < total_crimes_to_factor:
            crime = nearest_crimes[crime_index]
            crime_score += (crime.severity / crime.latlon.distance(latlon))
            crime_index += 1
        return crime_score

    def score_route(self, route, crime_neighborhood_percentage=0.01):
        return sum([self.score_location(latlon, crime_neighborhood_percentage) for latlon in route.latlons])


def read_crimes(csv_file_path):
    crimes = []
    with open(csv_file_path, "r") as csv_file:
        for line in csv_file:
            tokens = line.split(",")

            severity = tokens[0]
            lat = tokens[1]
            lon = tokens[2]

            latlon = LatLon(float(lat), float(lon))
            crime = Crime(latlon, int(severity))
            crimes.append(crime)
    return crimes


def get_route_json(init_latlon, final_latlon):
    init_destination = str(init_latlon)
    final_destination = str(final_latlon)
    url = "http://www.mapquestapi.com/directions/v2/alternateroutes?" \
          "key={KEY}" \
          "&from={FROM}" \
          "&to={TO}" \
          "&maxRoutes={MAX_ROUTES}" \
          "&timeOverage={TIME_OVERAGE}"
    url = url.format(KEY=api_key,
               FROM=init_destination,
               TO=final_destination,
               MAX_ROUTES=10,
               TIME_OVERAGE=200)
    return urllib.request.urlopen(url).read()


def parse_route_json(route_json):
    json_routes = []
    json_routes.append(route_json["route"])
    json_routes.extend([alternate_route["route"] for alternate_route in route_json["route"]["alternateRoutes"]])

    def _extract_route_data(json_route):
        try:
            maneuvers = json_route["legs"][0]["maneuvers"]
            lats = []
            lons = []
            narratives = []
            for maneuver in maneuvers:
                start_point = maneuver["startPoint"]
                lats.append(start_point["lat"])
                lons.append(start_point["lng"])
                narratives.append(maneuver["narrative"])
            return lats, lons, narratives
        except Exception as e:
            print(e)
            return None, None, None

    routes = []
    for json_route in json_routes:
        lats, lons, narratives = _extract_route_data(json_route)
        if lats and lons and narratives:
            if len(lats) is not len(lons) is not len(narratives):
                raise Exception("length of lats, lons, and narratives must be equal")
            latlons = []
            for x in range(len(lats)):
                latlons.append(LatLon(lats[x], lons[x]))
            routes.append(Route(latlons, narratives))
        else:
            raise Exception("lats ({}) or lons ({}) or narratives ({}) is None".format(lats, lons, narratives))
    return routes


def draw_routes(routes, line_width="2"):
    colors = []
    for x, route in enumerate(routes):
        colors.append(int(255 * (x+1) / len(routes)))
    hex_colors = []
    for color in colors:
        hex_colors.append(hex(color)[-2:] + "0000")
    lowest_crime_score = math.inf
    lowest_crime_score_index = 0
    route_index = 0
    for route in routes:
        if route.crime_score < lowest_crime_score:
            lowest_crime_score = route.crime_score
            lowest_crime_score_index = route_index
        route_index += 1
    hex_colors[lowest_crime_score_index] = "00ff00"

    def _make_polyline(route, color):
        coordinates = ""
        for latlon in route.latlons:
            coordinates += "|{},{}".format(latlon.lat, latlon.lon)
        return "&shape=border:" + color + coordinates + "&size=@" + str(line_width) + "x"

    url_args = ""
    for route, hex_color in zip(routes, hex_colors):
        url_args += _make_polyline(route, hex_color)
    url = "https://www.mapquestapi.com/staticmap/v5/map?key=" + api_key + url_args
    map_response = BytesIO(urllib.request.urlopen(url).read())
    image = Image.open(map_response)
    image = image.crop((0, 0, image.width, image.height - 30))
    return image


def main():

    Tk().withdraw()
    crime_data_file = askopenfilename(filetypes=[("Comma Separated Values","*.csv")], title="Select city crime data file")

    crimes = read_crimes(crime_data_file)
    vector_crime_map = VectorCrimeMap(crimes)

    window = Tk()
    window.title("BMORE SAFE")

    Label(window, text="starting coordinates (Latitude,Longitude").grid(row=0)
    Label(window, text="ending coordinates (Latitude,Longitude)").grid(row=1)

    init_lat_entry = Entry(window)
    init_lon_entry = Entry(window)
    final_lat_entry = Entry(window)
    final_lon_entry = Entry(window)

    init_lat_entry.grid(row=0, column=1)
    init_lon_entry.grid(row=0, column=2)
    final_lat_entry.grid(row=1, column=1)
    final_lon_entry.grid(row=1, column=2)

    init_latlon_var = StringVar(window)
    init_latlon_var.set("Preset coords...")
    final_latlon_var = StringVar(window)
    final_latlon_var.set("Preset coords...")

    preset_destinations = {"Homewood Campus",
                           "Medical Campus",
                           "National Aquarium",
                           "BWI Airport",
                           "Cherry Hill"}

    preset_destination_coordinate_dict = {"Homewood Campus":LatLon(39.329903, -76.620522),
                                          "Medical Campus":LatLon(39.299681, -76.593301),
                                          "National Aquarium":LatLon(39.286736, -76.608363),
                                          "BWI Airport":LatLon(39.177213, -76.668371),
                                          "Cherry Hill":LatLon(39.2548293, -76.634412)}

    init_preset_destinations_dropdown = OptionMenu(window, init_latlon_var, "Preset coords...", *preset_destinations)
    final_preset_destinations_dropdown = OptionMenu(window, final_latlon_var, "Preset coords...", *preset_destinations)

    def _set_entry_text(entry, text):
        entry.delete(0, END)
        entry.insert(0, str(text))

    def _on_change_init_destination_from_dropdown(*args):
        latlon = preset_destination_coordinate_dict[init_latlon_var.get()]
        _set_entry_text(init_lat_entry, latlon.lat)
        _set_entry_text(init_lon_entry, latlon.lon)

    def _on_change_final_destination_from_dropdown(*args):
        latlon = preset_destination_coordinate_dict[final_latlon_var.get()]
        _set_entry_text(final_lat_entry, latlon.lat)
        _set_entry_text(final_lon_entry, latlon.lon)

    init_latlon_var.trace("w", _on_change_init_destination_from_dropdown)
    final_latlon_var.trace("w", _on_change_final_destination_from_dropdown)

    init_preset_destinations_dropdown.grid(row=0, column=3)
    final_preset_destinations_dropdown.grid(row=1, column=3)

    def _process_latlon_input():

        init_latlon = LatLon(float(init_lat_entry.get()), float(init_lon_entry.get()))
        final_latlon = LatLon(float(final_lat_entry.get()), float(final_lon_entry.get()))

        get_request_response = get_route_json(init_latlon, final_latlon)
        route_json = json.loads(get_request_response)
        routes = parse_route_json(route_json)

        for route in routes:
            route.crime_score = vector_crime_map.score_route(route)

        min_crime_score = math.inf
        min_crime_route = routes[0]
        for route in routes:
            if route.crime_score < min_crime_score:
                min_crime_score = min_crime_route.crime_score
                min_crime_route = route
        directions = ""
        direction_number = 1
        for narrative in min_crime_route.narratives:
            directions += str(direction_number) + ".  " + narrative + "\n\n"
            direction_number += 1
        draw_routes(routes).show()
        showinfo(title="Safest Directions", message=directions)

    Button(window, text="Go", command=_process_latlon_input).grid(row=3, column=0)

    mainloop()


if __name__ == "__main__":
    main()