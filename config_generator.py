import osmnx as ox
import random
import json
from geopy.distance import geodesic

# Function to generate random locations on roads
def generate_random_road_locations(G, n, min_distance_m):
    nodes = list(G.nodes)
    locations = []

    def is_valid_location(new_location, existing_locations, min_distance):
        for loc in existing_locations:
            if geodesic(new_location, loc).meters < min_distance:
                return False
        return True

    while len(locations) < n:
        node = random.choice(nodes)
        lat = G.nodes[node]['y']
        lon = G.nodes[node]['x']
        new_location = [lat, lon]
        if is_valid_location(new_location, locations, min_distance_m):
            locations.append(new_location)

    return locations

# Define the center location
center_location = (41.558058, -8.398085)  # Example center location

# Download the map around the center location
G = ox.graph_from_point(center_location, dist=3000, network_type='drive')  # Adjust 'dist' as needed

# Generate random trash locations on the roads
n_trashes = 40  # Number of trash locations
min_distance_m = 100  # Minimum distance between trash locations in meters
trash_positions = generate_random_road_locations(G, n_trashes, min_distance_m)

# Create the configuration dictionary
config = {
    "center_position": [41.558058, -8.398085],
    "number_of_collectors": 5,
    "number_of_trashes": n_trashes,
    "trash_positions": trash_positions,
    "truck_velocity": 50,
    "simulation_speed": 100,
    "trash_occupancy_per_hour": 20,
    "images_directory": "images/"
}

# Save the configuration to a file
config_path = 'config/config4.json'
with open(config_path, 'w') as config_file:
    json.dump(config, config_file, indent=4)

print(f"Configuration file saved to {config_path}")
