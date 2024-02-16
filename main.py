# Import necessary modules
from src.lstspred import LineStringConstructor, RoutePlan, TimeStampPredictor
import csv

# Function to load data from CSV
def load_csv_data(filename):
    with open(filename, mode='r', encoding='utf-8-sig') as myfile:
        reader = csv.DictReader(myfile)
        if 'timestamp' in reader.fieldnames:
            # If the CSV contains timestamps, load longitude, latitude, and timestamp
            return [(float(row.get('longitude')), float(row.get('latitude')), float(row.get('timestamp'))) for row in reader]
        else:
            # If no timestamp, load just longitude and latitude
            return [(float(row.get('longitude')), float(row.get('latitude'))) for row in reader]

# Load shape, schedule, and trip data from CSV files
shape = load_csv_data('example/data/shape.csv')
schedule = load_csv_data('example/data/schedule.csv')
trip = load_csv_data('example/data/trip.csv')

# Create a LineStringConstructor object with the shape data
my_line = LineStringConstructor(shape)

# Create RoutePlan objects for the schedule and trip data
my_schedule = RoutePlan(schedule, my_line)
my_trip = RoutePlan(trip, my_line)

# Initialize the TimeStampPredictor with the created RoutePlan objects
predictor = TimeStampPredictor(my_schedule, my_trip)

# Use the TimeStampPredictor to predict timestamps for the trip
my_pred = predictor.predict_schedule_by_trip()

# Save the prediction results to a CSV file
my_pred.to_csv('example/data/prediction_results.csv', index=False)

print("Prediction results have been saved to 'examples/data/prediction_results.csv'")
