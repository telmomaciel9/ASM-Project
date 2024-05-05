from spade import agent
from Behaviours.Collector.receivePath_Behav import ReceivePath_Behav
import threading
from Classes.Position import interpolate_points, Position
import time
from config import Config
from util import jid_to_name

class TrashCollector(agent.Agent):

    async def setup(self):
        print("Trash Collector Agent {}".format(str(self.jid)) + " starting...")
        
        self.collector_capacity = 500 # max collector capacity
        self.current_occupancy = 0 # current occupancy of the collector (max is collector_capacity)
        
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

        a = ReceivePath_Behav()
        #b = DisposeTrash_Behav()

        self.add_behaviour(a)
        #self.add_behaviour(b)

    def update_position(self, new_pos):
        with self.lock:
            self.position = new_pos

    def set_map(self, locations_map):
        print("Trash Collector: Set location map")
        self.locations_map = locations_map

    def go_to_position(self, route):
        def update_positions():
            start_position = self.position
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

    def get_best_path_rating(self, locations_map, trash_occupancies_dict):
        best_path, cost, routes = locations_map.find_best_path(trash_occupancies_dict, self.collector_capacity)
        rating = 0
        return best_path, cost, routes, rating
