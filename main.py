from flask import Flask, render_template, request
import pandas as pd
import math
import numpy as np
import pymongo
import logging

app = Flask(__name__)
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["routes"]
collections = db["collection"]

# logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.route('/')
def home():
    # app.logger.info('Home page accessed')
    return render_template("index.html")


@app.route('/about')
def about():
    # app.logger.info('About page accessed')
    return render_template("about.html")


@app.route('/discover')
def discover():
    # app.logger.info('Discover page accessed')
    return render_template("locations.html")


@app.route('/FlightRoutes')
def FlightRoutes():
    # app.logger.info('FlightRoutes page accessed')
    return render_template("register.html")


@app.route('/output', methods=['POST'])
def process_form():
    if request.method == 'POST':
        # app.logger.info('Form submitted')
        def calculate_distance_using_four_digit_code(airport_1, airport_2):
            # needed_data is dictionary. airport_1,airport_2 is four digits code for airport and key for needed_data.
            # Value of needed_data is longitude and latitude
            point1 = (needed_data[airport_1][0], needed_data[airport_1][1])
            point2 = (needed_data[airport_2][0], needed_data[airport_2][1])
            d = calculate_distance_using_coordinates(point1, point2)
            return d

        # Method To Calculate The Distance Between Two Coordinates
        def calculate_distance_using_coordinates(point1, point2):
            lat_1, long_1 = point1[0] * math.pi / 180, point1[1] * math.pi / 180
            lat_2, long_2 = point2[0] * math.pi / 180, point2[1] * math.pi / 180
            d = 3963.0 * np.arccos(
                (math.sin(lat_1) * math.sin(lat_2)) + math.cos(lat_1) * math.cos(lat_2) * math.cos(long_2 - long_1))
            d = d * 1.609344
            return d

        # Get a Coordination Of Nearest Point on Line From Airport
        def dis_from_source_and_destination(point1, point2, point3):
            x = calculate_distance_using_coordinates(point1, point3) + calculate_distance_using_coordinates(point2,
                                                                                                            point3)
            return x

        def find_closest_lesser_key(dictionary, target_value):
            closest_key = None
            min_difference = float('inf')  # Initialize with a large value

            for key, value in dictionary.items():
                if value < target_value:
                    difference = target_value - value
                    if difference < min_difference:
                        closest_key = key
                        min_difference = difference

            return closest_key

        # Load Data
        data = pd.read_csv("Data.csv")
        # data = data.head(1000)
        n = len(data)
        plane_max_capacity = 6000
        # Get Four Digit Code and It Coordinates
        needed_data = {}
        db_dic = {}
        for i in range(len(data)):
            needed_data[data["four_digit"][i]] = [data["l1"][i], data["l2"][i]]

        origin = request.form.get('origin').upper()
        source = origin
        destination = request.form.get('destination').upper()
        db_dic["source"] = source
        db_dic["destination"] = destination
        route = []
        try:
            # Coordinates Of Destination
            p2 = (needed_data[destination][0], needed_data[destination][1])

            on = True

            while on:

                if plane_max_capacity > calculate_distance_using_four_digit_code(source, destination):
                    app.logger.info("Done")
                    break

                # Coordinates Of Source
                p1 = (needed_data[source][0], needed_data[source][1])

                x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]

                # Coordinates for Creating Square on Earth
                x_coor = (min(x1, x2), (max(x1, x2)))
                y_coor = (min(y1, y2), (max(y1, y2)))

                # All Airports in Square
                airport_in_square = []

                # Get All Airport
                for i in range(n):
                    if x_coor[0] < data["l1"][i] < x_coor[1] \
                            and y_coor[0] < data["l2"][i] < y_coor[1]:
                        airport_in_square.append(data["four_digit"][i])

                # Distance From Diagonal of Source and Destination
                dis = {}
                for i in range(len(airport_in_square)):
                    p3 = (needed_data[airport_in_square[i]][0], needed_data[airport_in_square[i]][1])
                    x = dis_from_source_and_destination(p1, p2, p3)
                    dis[airport_in_square[i]] = x
                dis = dict(sorted(dis.items(), key=lambda item: item[1]))

                new_dic = {}
                for key in dis:
                    a = calculate_distance_using_four_digit_code(key, source)
                    if plane_max_capacity > a:
                        new_dic[key] = a

                source = find_closest_lesser_key(new_dic, plane_max_capacity)
                if source is None:
                    break
                # VEHK
                # SBIT

                # for key in new_dic:
                #     if plane_max_capacity > calculate_distance_using_four_digit_code(key, source):
                #         source = key
                #         break

                route.append(source)
            if len(route) == 0:
                route.append("No Layovers Needed")
            db_dic["LayOvers"] = route
            collections.insert_one(db_dic)
            # app.logger.info('Processing complete')
            return render_template('output.html', origin=origin, destination=destination, route=route)

        except KeyError:
            db_dic["Error"] = "Incorrect Input"
            collections.insert_one(db_dic)
            # app.logger.error('Error: Incorrect Input')
            return render_template('error.html')


if __name__ == "__main__":
    app.run(debug=True)
