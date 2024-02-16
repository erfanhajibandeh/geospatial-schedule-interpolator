from shapely.geometry import LineString, Point
from geopy.distance import geodesic
import pandas as pd
import numpy as np

class LineStringConstructor:
    """
    A class to construct a line string from an ordered list of coordinate tuples and provide 
    functionality to project points onto the line string and calculate distances along it.

    Attributes:
        points (list of tuples): The list of (longitude, latitude) tuples defining the line string.
        line_string (LineString): The LineString object created from the points.
    """
    
    def __init__(self, points=None):
        """
        Initializes the LineStringConstructor with a list of points.

        Parameters:
            points (list of tuples): A list of (longitude, latitude) tuples. Defaults to an empty list.

        Raises:
            ValueError: If the points do not meet the requirements (at least two points, must be tuples of floats).
        """
        if points is None:
            points = []
            
        if not self._validate_points(points):
            raise ValueError('Points must be a list of tuples (longitude, latitude) with floats.')

        if len(points) < 2:
            raise ValueError('Minimum of two points are required to construct a line string')
        
        self.points = points
        self.line_string = self._create_line_string()
        
    def project_and_calculate_distance(self, df):
        """
        Calculate distances along a line string for points in a grouped DataFrame.
        This function iterates over each segment of the line string. For each segment, it checks if the projected point 
        lies on that segment or is very close to it (within a threshold of 0.0001 units). If the projected point is on 
        the segment or close enough, the function calculates the geodesic distance from the start of the line string to 
        the projected point and breaks the loop. If the projected point is not on the segment, the function adds the 
        geodesic distance of the segment to the total distance. The process continues until the segment containing the 
        projected point is found or all segments are traversed.

        :param group: DataFrame group for a single trip, sorted by occurrence.
        :param line_string: LineString object for the trip.

        :return: List of distances or None for each point in the group.
        """
        
        last_segment_index = -1
        cumulative_distance = 0.0 
        distances = []

        for _, row in df.iterrows():
            point = Point(row['longitude'], row['latitude'])
            projected_point = self.line_string.interpolate(self.line_string.project(point))
            point_found = False


            for i in range(last_segment_index + 1, len(self.line_string.coords) - 1):
                segment = LineString([self.line_string.coords[i], self.line_string.coords[i + 1]])
                
                # Check if point is on the segment, if yes calculate distance to the point
                if segment.contains(projected_point) or segment.distance(projected_point) < 0.0001:  
                    if i > 0 and last_segment_index < i:
                        #calculate distance to the segment
                        for j in range(last_segment_index + 1, i):
                            cumulative_distance += geodesic(self.line_string.coords[j][::-1], self.line_string.coords[j + 1][::-1]).kilometers

                    last_segment_index = i
                    #calculate distance in the segment to the point
                    segment_start_to_point_distance = geodesic(self.line_string.coords[i][::-1], (projected_point.y, projected_point.x)).kilometers
                    total_distance = cumulative_distance + segment_start_to_point_distance
                    #record the distance and skip the previous segments for the next point - this is to improve seatch efficiency
                    distances.append(total_distance)
                    point_found = True
                    #calculate total distance to the point
                    cumulative_distance += geodesic(self.line_string.coords[i][::-1], self.line_string.coords[i + 1][::-1]).kilometers
                    break
                
            # Point did not project onto the line string correctly mainly because the point is near where the line string intersects iteself or there are overlaping parts
            if not point_found:
                distances.append(None)  

        return pd.Series(distances)

    def _create_line_string(self):
        """
        Creates a LineString object from the provided points.

        Returns:
            LineString: The LineString object created from the points.
        """
        return LineString(self.points)

    def _validate_points(self, points):
        """
        Validates the input list of points to ensure it meets the criteria for constructing a line string.

        Parameters:
            points (list): The list of point tuples to validate.

        Returns:
            bool: True if the points are valid, False otherwise.
        """
        if not isinstance(points, list):
            return False

        for point in points:
            if not (isinstance(point, tuple) and len(point) == 2 and 
                    all(isinstance(coordinate, float) for coordinate in point)):
                return False

        return True
    
class RoutePlan:
    """
    A class to create a schedule or trip plan based on geotagged points with timestamps,
    utilizing a provided line string for spatial reference.

    Attributes:
        points (list of tuples): The list of geotagged points (longitude, latitude, timestamp).
        line_string (LineStringConstructor): An instance of LineStringConstructor for projecting points.
        geotagged_timestamps (DataFrame): A DataFrame holding the processed schedule or trip information.
    """
    
    def __init__(self, points=None, line_string_object=None):
        """
        Initializes the RoutePlan with geotagged points and a line string object.

        Parameters:
            points (list of tuples): A list of geotagged points (longitude, latitude, timestamp).
            The coordinates should be float and the timestamp should be in epoch style and float. 
            line_string_object (LineStringConstructor, optional): An instance of LineStringConstructor.

        Raises:
            ValueError: If the points do not meet the requirements.
            TypeError: If the line_string_object is not an instance of LineStringConstructor.
        """
        if points is None:
            points = []
        
        if not self._validate_geotagged_timestamp(points):
            raise ValueError('Points must be a list of tuples (longitude, latitude, timestamp) with floats.')

        if line_string_object is not None and not isinstance(line_string_object, LineStringConstructor):
            raise TypeError('line_string must be an instance of LineStringConstructor')
        
        self.points = points
        self.line_string = line_string_object
        self.geotagged_timestamps = self.create_geotagged_timestamp()
    
    def create_geotagged_timestamp(self):
        """
        Processes the geotagged points to create a schedule with distances traveled along the line string.

        Returns:
            DataFrame: A pandas DataFrame with geotagged points and distances traveled.
        """
        schedule = pd.DataFrame(self.points, columns=['longitude', 'latitude', 'timestamp'])
        schedule = schedule.sort_values(by=['timestamp'], ascending=True)
        schedule['distance_traveled'] = self.line_string.project_and_calculate_distance(df=schedule)

        return schedule
    
    def _validate_geotagged_timestamp(self, schedule_points):
        """
        Validates the input list of geotagged points to ensure it meets the requirements for a schedule.

        Parameters:
            schedule_points (list): The list of geotagged point tuples to validate.

        Returns:
            bool: True if the points are valid, False otherwise.
        """
        if not isinstance(schedule_points, list):
            return False

        for geotagged_timestamp in schedule_points:
            if not (isinstance(geotagged_timestamp, tuple) and len(geotagged_timestamp) == 3 and 
                    all(isinstance(data, float) for data in geotagged_timestamp)):
                return False

        return True
    
class TimeStampPredictor:
    """
    A class for predicting timestamps for a trip's geotagged points by interpolating from a schedule
    using weighted interpolation based on distances traveled along a line string.

    Attributes:
        schedule (DataFrame): A DataFrame with the schedule's geotagged timestamps and distances.
        trip (DataFrame): A DataFrame with the trip's geotagged timestamps and distances.
    """
    
    def __init__(self, schedule=None, trip=None):
        """
        Initializes the TimeStampPredictor with a schedule and a trip RoutePlan.

        Parameters:
            schedule (RoutePlan): A RoutePlan object for the schedule.
            trip (RoutePlan): A RoutePlan object for the trip.

        Raises:
            TypeError: If either schedule or trip is not an instance of RoutePlan.
        """
        if schedule is not None and not isinstance(schedule, RoutePlan):
            raise TypeError('schedule must be an instance of RoutePlan')
        
        if trip is not None and not isinstance(trip, RoutePlan):
            raise TypeError('trip must be an instance of RoutePlan')
        
        self.schedule = schedule.geotagged_timestamps
        self.trip = trip.geotagged_timestamps
        
    def predict_schedule_by_trip(self):
        """
        Predicts timestamps for the trip's geotagged points by interpolating from the schedule's geotagged epoch timestamps.
        This method uses a weighted interpolation mechanism based on distances traveled along a line string.

        The prediction process involves several steps:
        1. Merging the schedule and trip dataframes, sorted by the distance traveled.
        2. Calculating the 'inverse_speed' between consecutive schedule points as the ratio of time difference (epoch difference) to distance traveled.
        3. Forward filling the 'inverse_speed' to apply it for interpolation between known schedule timestamps.
        4. Interpolating timestamps for trip points based on the weighted duration between the closest known schedule timestamps.
        5. Handling edge cases where trip points fall outside the range of the schedule points.

        Returns:
            DataFrame: A pandas DataFrame containing the original trip points with additional columns for 'predicted_timestamp',
                       'dist_to_closest_ts', and 'time_to_closest_ts', indicating the predicted timestamp for each point, the distance
                       to the closest known timestamp, and the time difference to the closest known timestamp, respectively. Additionally,
                       'trip_to_schedule_ts_ratio' reports the total number of trip timestamps to schedule timestamps.
        """  
        
        predict_df = self.schedule.reset_index(drop=False)
        predict_df = predict_df[~predict_df['distance_traveled'].isna()]
        predict_df.rename(columns = {'timestamp':'schedule_timestamp'},inplace=True)
        predict_df['inverse_speed'] = predict_df['schedule_timestamp'].diff(1).shift(-1) / predict_df['distance_traveled'].diff(1).shift(-1)
        predict_df = pd.concat([predict_df,self.trip],axis=0).sort_values(by='distance_traveled',kind='mergesort').reset_index(drop=True)
        predict_df['inverse_speed'] = predict_df['inverse_speed'].fillna(method='ffill')
        predict_df['weighted_duration'] = predict_df['distance_traveled'].diff().shift(-1)*predict_df['inverse_speed']
        predict_df['predicted_timestamp'] = predict_df['timestamp']
        predict_df['dist_to_closest_ts'] = np.nan
        predict_df['time_to_closest_ts'] = np.nan
        trip_intermediate_timestamp_indexes = predict_df[~predict_df['timestamp'].isna()].index
        trip_begining_tail_indexes = np.arange(0,trip_intermediate_timestamp_indexes.min())
        trip_ending_tail_indexes = np.arange(trip_intermediate_timestamp_indexes.max()+1,predict_df.shape[0])

        #Intermediate forward propagation of the timestamps for schedule locations between two reported timestamps, if any.
        for current_ts,next_ts in enumerate(trip_intermediate_timestamp_indexes):
            if next_ts == trip_intermediate_timestamp_indexes.max():
                break
            interval_last_ts = trip_intermediate_timestamp_indexes[current_ts+1]
            if interval_last_ts - trip_intermediate_timestamp_indexes[current_ts] == 1:
                pass
            else:
                interval_total_duration = predict_df['timestamp'].iloc[interval_last_ts] - predict_df['timestamp'].iloc[next_ts]
                interval_weighted_duration = predict_df['weighted_duration'].iloc[next_ts:interval_last_ts].sum()
                for unknown_timestamp in range(next_ts+1,interval_last_ts):
                    prev_ts = unknown_timestamp - 1
                    current_dist = predict_df['distance_traveled'].iloc[unknown_timestamp]
                    prev_dist = predict_df['distance_traveled'].iloc[prev_ts]
                    prev_speed = predict_df['inverse_speed'].iloc[prev_ts]
                    
                    predict_df.at[unknown_timestamp, 'predicted_timestamp'] = \
                        predict_df.at[prev_ts, 'predicted_timestamp'] + \
                        interval_total_duration * prev_speed * (current_dist - prev_dist) / interval_weighted_duration
                    
                    forward_dist_to_closest_ts = np.abs(predict_df['predicted_timestamp'].iloc[interval_last_ts] - predict_df['predicted_timestamp'].iloc[unknown_timestamp])
                    backward_dist_to_closest_ts = np.abs(predict_df['predicted_timestamp'].iloc[next_ts] - predict_df['predicted_timestamp'].iloc[unknown_timestamp])

                    forward_time_to_closest_ts = np.abs(predict_df['timestamp'].iloc[interval_last_ts] - predict_df['predicted_timestamp'].iloc[unknown_timestamp])
                    backward_time_to_closest_ts = np.abs(predict_df['timestamp'].iloc[next_ts] - predict_df['predicted_timestamp'].iloc[unknown_timestamp])

                    predict_df.at[unknown_timestamp, 'dist_to_closest_ts'] = \
                        np.where(forward_dist_to_closest_ts <= backward_dist_to_closest_ts, forward_dist_to_closest_ts, backward_dist_to_closest_ts)
                    
                    predict_df.at[unknown_timestamp, 'time_to_closest_ts'] = \
                        np.where(forward_time_to_closest_ts <= backward_time_to_closest_ts, forward_time_to_closest_ts, backward_time_to_closest_ts)

        #Backward propagation of the timestamps for schedule locations between the begining of the trip and the first trip timestamp, if any.
        if len(trip_begining_tail_indexes) > 0:
            backward_dist_to_closest_ts = 0
            backward_time_to_closest_ts = 0
            for unknown_timestamp in trip_begining_tail_indexes[::-1]:
                next_ts = unknown_timestamp + 1
                current_dist = predict_df['distance_traveled'].iloc[unknown_timestamp]
                next_dist = predict_df['distance_traveled'].iloc[next_ts]
                current_speed = predict_df['inverse_speed'].iloc[unknown_timestamp]
                    
                predict_df.at[unknown_timestamp, 'predicted_timestamp'] = \
                    predict_df.at[next_ts, 'predicted_timestamp'] - \
                    current_speed * (next_dist - current_dist) 
                
                backward_dist_to_closest_ts += np.abs(next_dist - current_dist)
                backward_time_to_closest_ts += np.abs(predict_df['predicted_timestamp'].iloc[next_ts] - predict_df['predicted_timestamp'].iloc[unknown_timestamp])
                
                predict_df.at[unknown_timestamp, 'dist_to_closest_ts'] = backward_dist_to_closest_ts
                predict_df.at[unknown_timestamp, 'time_to_closest_ts'] = backward_time_to_closest_ts
                
        #Forward propagation of the timestamps for schedule locations between the end of the trip and the last trip timestamp, if any.
        if len(trip_ending_tail_indexes) > 0 :
            forward_dist_to_closest_ts = 0
            forward_time_to_closest_ts = 0        
            for unknown_timestamp in trip_ending_tail_indexes:
                prev_ts = unknown_timestamp - 1
                current_dist = predict_df['distance_traveled'].iloc[unknown_timestamp]
                prev_dist = predict_df['distance_traveled'].iloc[prev_ts]
                prev_speed = predict_df['inverse_speed'].iloc[prev_ts]
                    
                predict_df.at[unknown_timestamp, 'predicted_timestamp'] = \
                    predict_df.at[prev_ts, 'predicted_timestamp'] + \
                    prev_speed * (current_dist - prev_dist) 

                forward_dist_to_closest_ts += np.abs(current_dist - prev_dist)
                forward_time_to_closest_ts += np.abs(predict_df['predicted_timestamp'].iloc[unknown_timestamp] - predict_df['predicted_timestamp'].iloc[prev_ts])
                
                predict_df.at[unknown_timestamp, 'dist_to_closest_ts'] = forward_dist_to_closest_ts
                predict_df.at[unknown_timestamp, 'time_to_closest_ts'] = forward_time_to_closest_ts


        predict_df['trip_to_schedule_ts_ratio'] = np.round((predict_df['index'].isna().sum() / predict_df['index'].notna().sum()),2)

        predict_df.drop(columns=['schedule_timestamp','weighted_duration','timestamp','inverse_speed'],inplace=True)
        predict_df.dropna(subset=['index'],inplace=True)
        predict_df.drop(columns=['index'],inplace=True)
        predict_df.reset_index(drop=True,inplace=True)
    
        return predict_df
