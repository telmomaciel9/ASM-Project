
from spade.behaviour import PeriodicBehaviour
from spade.message import Message

import asyncio
import json
from util import jid_to_name

# total trash occupancy threshold
total_occupancy_threshold = 100

class ProposeCollectors_Behav(PeriodicBehaviour):
    async def run(self):
        self.collector_proposals = {}

        # If the trash occupancy of all trashes combined subtracted by the total capacity of collectors on the road excedes the threshold, we send a collector
        if (sum(list(self.agent.trash_occupancies.values())) - self.agent.get_collector_capacity_on_the_road()) > total_occupancy_threshold and self.agent.get_number_of_available_collectors() >= 0:
            # get the jids of the available collectors
            available_collectors_jids = self.agent.get_available_collectors_jids()
            for collector_jid in available_collectors_jids:
                # for each collector, issue a call for proposals
                msg = Message(to=collector_jid)
                # issue a call for proposals. Center requests proposals from the collectors, to get the best proposal
                msg.set_metadata("performative", "cfp")
                excluded_locations = self.agent.get_excluded_paths()
                data = {
                    "trash_occupancies_dict": self.agent.trash_occupancies,
                    "excluded_locations": excluded_locations,
                }
                msg.body = json.dumps(data)
                await self.send(msg)

            # Schedule a check function, to check for the best rating after one second
            asyncio.create_task(self.check_collector_paths(1))


    """
    This function goes over the collector_proposals dictionary, gets the collector with the highest rating, and requests the collector to go on
    the designated path
    """
    async def check_collector_paths(self, delay_seconds):
        """Wait for a delay and then process the collected paths."""
        await asyncio.sleep(delay_seconds)

        if self.agent.collector_proposals:
            # Find the collector with the best rating
            best_collector_jid, (best_rating, best_path, routes) = min(self.agent.collector_proposals.items(), key=lambda x: x[1][0])
            self.agent.collector_proposals = {}
            print(f"Center: Accepting proposal of {jid_to_name(best_collector_jid)}")
            await self.request_collector(best_collector_jid, best_path, routes)
        else:
            print("Center: No collectors have responded with a path.")

    """
    Given the jid of a collector, a path, and a route, request the collector to go on the specified path route
    """
    async def request_collector(self, collector_jid, path, routes):
        # set the trash collector availability to False, because it is going to be used for the next collection
        self.agent.set_collector_availability(collector_jid, False, path)
        # get the best path from the central to the trashes and back
        data = {
            "path": path,
            "routes": routes,
        }
        # create the message with destination to the trash collector
        msg = Message(to=collector_jid)
        # the body of the message contains only the path of the trash collector
        msg.body = json.dumps(data)
        msg.set_metadata("performative", "accept-proposal") # set the message metadata
        await self.send(msg) # send msg to trash collector