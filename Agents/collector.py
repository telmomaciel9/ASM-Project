from spade import agent
from Behaviours.Collector.receiveMessages_Behav import ReceiveMessages_Behav
import threading
from Classes.Position import interpolate_points, Position
import time
from config import Config

class TrashCollector(agent.Agent):

    async def setup(self):
        print("Trash Collector Agent {}".format(str(self.jid)) + " starting...")
        
        #self.collector_capacity = 500 # max collector capacity
        self.current_occupancy = 0 # current occupancy of the collector (max is collector_capacity)
        self.gas_per_100km = 10 # gas spent per 100km
        
        if self.get("position"):
            self.position = self.get("position")
        else:
            print(f"Trash Collector Agent {self.jid}: position not defined!")
            
        if self.get("positions"):
            self.jid_to_position_dict = self.get("positions")
        else:
            print(f"Trash Collector Agent {self.jid}: positions dict not defined!")

        config = Config()
        self.jump_size = config.jump_size
        self.update_interval = config.update_interval

        self.lock = threading.Lock()  # A lock to synchronize access to the position

        a = ReceiveMessages_Behav()

        self.add_behaviour(a)

    def update_position(self, new_pos):
        with self.lock:
            self.position = new_pos

    def set_map(self, locations_map):
        print("Trash Collector: Set location map")
        self.locations_map = locations_map

    def go_to_position(self, route):
        def update_positions():
            start_position = self.position
            if route:
                for route_pos in route:
                    end_position = Position(*route_pos)
                    interpolated_positions = interpolate_points(start_position, end_position, self.jump_size)
                    for pos in interpolated_positions:
                        self.update_position(pos) # update position of the trash collector
                        time.sleep(self.update_interval)
                    start_position = end_position

        # execute position updates in a new thread, so as to not block the execution
        thread = threading.Thread(target=update_positions)
        thread.daemon = True  # Set as a daemon so it will automatically close when the main program exits
        thread.start()

    def get_best_path_rating(self, trash_occupancies_dict, excluded_locations):
        total_occupancy = sum(list(trash_occupancies_dict.values()))
        best_path, cost, routes = self.locations_map.find_best_path(trash_occupancies_dict, self.collector_capacity, excluded_locations)
        rating = self.calculate_rating(total_occupancy)
        return best_path, cost, routes, rating

    def get_route_to_central(self, current_jid=None):
        if not current_jid:
            return []
        return self.locations_map.get_route(current_jid)

    # returns the rating of this trash collector given the total trash occupancy
    def calculate_rating(self, total_occupancy):
        return self.gas_per_100km + abs(total_occupancy - self.collector_capacity)
