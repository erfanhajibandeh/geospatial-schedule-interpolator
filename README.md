# GeoSpatial Schedule Interpolator 

## Overview

This project provides a Python module designed for analyzing and predicting schedules for delivery or transportation routes with fixed stops. By accepting an ordered tuple of locations to define a line string, the module can process schedules and predict schedule times for specific locations based on weighted interpolation of reported timestamps along that line string. It is particularly useful for applications in delivery services, public transportation, and any scenario involving fixed routes and schedules.

## Installation

To use this project, you'll need Python installed on your system. This project has been tested with Python 3.8+, but it may work with other versions. You can install the required dependencies with pip:

pip install -r requirements.txt


This command will install all necessary libraries, including Shapely, GeoPy, Pandas, and NumPy, as specified in the `requirements.txt` file.

## Usage

First, import the module in your Python script:

```python
from src.lstspred import LineStringConstructor
from src.lstspred import RoutePlan
from src.lstspred import TimeStampPredictor

##Defining a Line String
Create a line string by providing an ordered list of tuples, each representing a location's longitude and latitude:

locations = [(longitude1, latitude1), (longitude2, latitude2), ...]
line_string = LineStringConstructor(locations)

##Creating a Schedule
Define a schedule with locations and timestamps:

schedule = [(longitude1, latitude1, timestamp1), (longitude2, latitude2, timestamp2), ...]
route_plan = RoutePlan(schedule, line_string)

##Predicting Schedule Times
To predict schedule times based on a trip's reported timestamps:

trip = [(longitude1, latitude1, timestamp1), (longitude2, latitude2, timestamp2), ...]
trip_plan = RoutePlan(trip, line_string)
predictor = TimeStampPredictor(route_plan, trip_plan)
predicted_schedule = predictor.predict_schedule_by_trip()

##Contributing

Contributions to this project are welcome! If you have suggestions for improvements or encounter any issues, please feel free to open an issue or submit a pull request.

##License

This project is licensed under the MIT License - see the LICENSE file for details.


