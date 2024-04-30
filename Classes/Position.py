# Class that represents a location in the map
from dataclasses import dataclass
import math

pos_equal_threshold = 0.0005

@dataclass
class Position:
    latitude: float
    longitude: float

    def __eq__(self, otherPos):
        distance = coords_distance(self.latitude, self.longitude, otherPos.latitude, otherPos.longitude)
        return distance < pos_equal_threshold
        #return self.latitude == otherPos.latitude and self.longitude == otherPos.longitude

    def __str__(self):
        return "Latitude: " + str(self.latitude) + "; Longitude: " + str(self.longitude)

    def __getitem__(self, arg):
        if arg==0:
            return self.latitude
        elif arg==1:
            return self.longitude
        else:
            print("Invalid Position index!")
            return None

    def tuple(self):
        return (self.latitude, self.longitude)

def interpolate_points(p1: Position, p2: Position, jump_size: float):
    #jump_size = 0.0001
    distance = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5
    num_points = math.ceil(distance / jump_size) # get number of jumps between the two locations.
    """ Interpolate `num_points` equally spaced points between p1 and p2. """
    if num_points == 0: # the points are the same
        interpolation = [p1]
    else:
        interpolation = [Position(p1[0] + i * (p2[0] - p1[0]) / num_points, p1[1] + i * (p2[1] - p1[1]) / num_points) for i in range(num_points + 1)]
    return interpolation

def coords_distance(lat1, lon1, lat2, lon2):
    # Assuming a flat Earth, use Pythagorean theorem
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)

def euclidean_dist_vec(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Assuming a flat Earth, use Pythagorean theorem
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)