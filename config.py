import json
import math

class Config:
    _instance = None

    def __new__(cls, config_file=None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            if config_file is None:
                print("Error generating config object")
            else:
                cls._instance.load_config(config_file)
        return cls._instance

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
            try:
                self.n_collectors = config['number_of_collectors']
                self.n_trashes = config['number_of_trashes']
                self.center_position = config['center_position']
                self.trash_positions = config['trash_positions']
                self.truck_velocity = config['truck_velocity']
                self.simulation_speed = config['simulation_speed']
                self.trash_occupancy_per_hour = config['trash_occupancy_per_hour']
                self.images_directory = config['images_directory']
                self.collector_capacities = config['collector_capacities']
                self.collectors_gas_per_100km = config['gas_per_100km']
                self.calculate_simulation_parameters()
            except KeyError:
                print("Error: Config didn't have all necessary values")
                return False
            return True

    def calculate_simulation_parameters(self):
        velocity_km_per_second = self.truck_velocity / 3600  # convert km/h to km/s
        trash_occupancy_per_second = self.trash_occupancy_per_hour / 3600
        latlon_to_km = 1 / 111
        self.jump_size = velocity_km_per_second * latlon_to_km
        self.update_interval = 1 / self.simulation_speed
        self.trash_occupancy_per_simulation_second = trash_occupancy_per_second * self.simulation_speed

    def get_jump_size(self):
        return self.jump_size

    def get_update_interval(self):
        return self.update_interval

    def get_trash_occupancy_per_simulation_second(self):
        return self.trash_occupancy_per_simulation_second
