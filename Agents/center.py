from spade import agent
from spade.template import Template
import datetime

from logs import log_center  # Import the logging function

from Behaviours.Center.receiveMessages_Behav import ReceiveMessages_Behav
from Behaviours.Center.proposalsCollectors_Behav import ProposeCollectors_Behav

"""
In the simulation, there is only one collection center.
"""
class CollectionCenter(agent.Agent):

    # dict that maps trash jids to their trash occupancy in kg
    trash_occupancies = {}
    # dict that maps trash jids to the time in seconds since they were last collected
    elapsed_time_collection = {}
    # dict that maps collector jids to their remaining capacities
    collector_remaining_capacities = {}
    # maps collectors jids to booleans that represent the collectors availability. If False, collector is currently collecting trash
    available_collectors = {}
    # maps the jid of collectors to the path they are currently collecting trash
    collector_to_path = {}

    async def setup(self):
        log_center(str(self.jid), "starting...")

        if self.get("position"):
            self.position = self.get("position")
        else:
            log_center(str(self.jid), "position not defined!")

        a = ReceiveMessages_Behav()

        # create a template so that the ReceiveMessages Behaviour can't receive proposals
        complement_template = Template(metadata={"performative": "propose"})
        self.add_behaviour(a, ~complement_template) # add the complement of the template so that it can't receive proposals

    def start_requesting_collectors(self):
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=5)
        b = ProposeCollectors_Behav(period = 3, start_at = start_at) # run every 3 seconds
        self.add_behaviour(b)


    def get_available_collector_jid(self):
        for (collector_jid, is_available) in self.available_collectors.items():
            if is_available:
                return collector_jid
        return None

    def get_available_collectors_jids(self):
        collector_jids = []
        for (collector_jid, is_available) in self.available_collectors.items():
            if is_available:
                collector_jids.append(collector_jid)
        return collector_jids

    def set_map(self, locations_map):
        log_center(str(self.jid), "Set location map")
        self.locations_map = locations_map

    # receives array with trash collector agents and maps their jids to whether or not they are being used on the road (boolean)
    def set_collectors(self, collector_jids):
        self.jid_to_collector = {}
        for collector_jid in collector_jids:
            self.available_collectors[collector_jid] = True

    def set_collector_availability(self, collector_jid, availability, path=None):
        self.available_collectors[collector_jid] = availability
        if availability:
            self.collector_to_path.pop(collector_jid, None)
        elif not availability and path:
            # collector is sent on this path
            self.collector_to_path[collector_jid] = path

    def get_excluded_paths(self):
        # return the paths that colletors are currently going through
        concatenated_set = sum(self.collector_to_path.values(), [])
        return concatenated_set

    def update_excluded_locations(self, collector_jid, collector_location_jid, remaining_capacity):
        if collector_location_jid != self.jid:
            collector_path = self.collector_to_path.get(collector_jid, None)
            if collector_path:
                # Find the index of the current location of the collector in the path
                try:
                    current_index = collector_path.index(collector_location_jid)
                except ValueError:
                    return  # If the current location is not in the path, exit the function

                # Calculate the cumulative occupancy from the current location to the end of the path
                cumulative_occupancy = 0
                updated_path = collector_path[:current_index + 1]  # Keep the path up to the current location

                for jid in collector_path[current_index + 1:]:
                    occupancy = self.trash_occupancies.get(jid, 0)
                    if cumulative_occupancy + occupancy <= remaining_capacity:
                        cumulative_occupancy += occupancy
                        updated_path.append(jid)
                    else:
                        # add the last element to the collector path so that it goes back to the central
                        updated_path.append(collector_path[-1])
                        break  # Stop adding to the path if the remaining capacity is exceeded

                # Update the path for the collector
                self.collector_to_path[collector_jid] = updated_path


    def get_number_of_available_collectors(self):
        num_available_collectors = 0
        for available in list(self.available_collectors.values()):
            if available:
                num_available_collectors += 1
        return num_available_collectors

    def get_collector_capacity_on_the_road(self):
        # returns the total capacity of the collectors on the road
        total_capacity = 0
        for collector_jid, remaining_capacity in self.collector_remaining_capacities.items():
            availability = self.available_collectors[collector_jid]
            if not availability:
                # we only count if the availability of the collector is False. This way the collector is on the road
                total_capacity += remaining_capacity
        return total_capacity

    def get_best_path(self, elapsed_time_collection, excluded_locations):
        # best_path is an array which contains the jid's of the agents in the path
        # cost_array is an array which contains the cost of each transition in the path
        best_path, cost_array, routes_array = self.locations_map.find_best_path(self.trash_occupancies, elapsed_time_collection, excluded_locations, collector_capacity=None)
        return best_path, cost_array, routes_array

