from spade import agent

from Behaviours.Center.receiveMessages_Behav import ReceiveMessages_Behav
from Behaviours.Center.proposalsCollectors_Behav import ProposeCollectors_Behav

"""
In the simulation, there is only one collection center.
"""
class CollectionCenter(agent.Agent):

    trash_occupancies = {}
    # maps collectors jids to booleans
    available_collectors = {}
    jid_to_collector = {}
    collector_proposals = {} # dictionary that stores the path proposals of the trash collectors
    collector_to_path = {} # maps the jid of collectors to the path they are currently collecting trash

    async def setup(self):
        print("Collection Center Agent {}".format(str(self.jid)) + " starting...")
        
        if self.get("position"):
            self.position = self.get("position")
        else:
            print("Collection Center: position not defined!")

        a = ReceiveMessages_Behav()
        b = ProposeCollectors_Behav(period = 5) # run every 5 seconds

        self.add_behaviour(a)
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
        print("Collection Center: Set location map")
        self.locations_map = locations_map

    # receives array with trash collector agents and maps their jids to whether or not they are being used on the road (boolean)
    def set_collectors(self, trash_collectors):
        self.jid_to_collector = {}
        for collector in trash_collectors:
            collector_jid = str(collector.jid)
            self.available_collectors[collector_jid] = True
            self.jid_to_collector[collector_jid] = collector

    def set_collector_availability(self, collector_jid, availability, path=None):
        self.available_collectors[collector_jid] = availability
        if availability:
            self.collector_to_path.pop(collector_jid)
        elif not availability and path:
            # collector is sent on this path
            self.collector_to_path[collector_jid] = path

    def get_excluded_paths(self):
        # return the paths that colletors are currently going through
        concatenated_set = sum(self.collector_to_path.values(), [])
        return concatenated_set

    def get_number_of_available_collectors(self):
        num_available_collectors = 0
        for available in list(self.available_collectors.values()):
            if available:
                num_available_collectors += 1
        return num_available_collectors

    def get_collector_capacity_on_the_road(self):
        # returns the total capacity of the collectors on the road
        total_capacity = 0
        for collector_jid, available in self.available_collectors.items():
            if not available:
                # we only count if the availability of the collector is False. This way the collector is on the road
                collector = self.jid_to_collector[collector_jid]
                collector_capacity = collector.collector_capacity
                total_capacity += collector_capacity
        return total_capacity


    def get_best_path(self, trash_occupancies_dict, collector_capacity):
        # best_path is an array which contains the jid's of the agents in the path
        # cost_array is an array which contains the cost of each transition in the path
        best_path, cost_array, routes_array = self.locations_map.find_best_path(trash_occupancies_dict, collector_capacity)
        return best_path, cost_array, routes_array

