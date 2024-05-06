"""
Trash Collector agent Behaviour 
This behaviour is responsible for receiving trash collection order from the central (in the form of a message containing a Path), and collecting the trash
This behaviour is also responsible for receiving the amount of trash to dispose from the Trash agents, and "disposing" it
"""

from spade.message import Message
from spade.behaviour import CyclicBehaviour

from util import jid_to_name
import time
import asyncio  # Import asyncio for asyncio.sleep
import json

class ReceivePath_Behav(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=10) # wait for a message for 10 seconds
        
        if msg:
            # Message Threatment based on different ACLMessage performatives
            performative = msg.get_metadata("performative")
            data = json.loads(msg.body)  # deserialize JSON back to a path
            if performative == 'accept-proposal': # Handle request to go collect trash in a path
                path = data["path"]
                routes = data["routes"]

                if path[0] == str(self.get('center_jid')):
                    # if the first location is the collection center, remove this from the path (because the trash collector starts there)
                    path.pop(0)

                path_route = list(zip(path, routes))

                for next_location, route in path_route:
                    # go to next_location
                    print("{}: Going to {}".format(self.agent.name, jid_to_name(next_location)))
                    destination_pos = self.agent.jid_to_position_dict[next_location]
                    self.agent.go_to_position(route)
                    #self.agent.go_to_position(destination_pos)
                    while self.agent.position != destination_pos:
                        await asyncio.sleep(0.1)  # Use asyncio.sleep instead of time.sleep

                    # now that we are at the next trash's location, we inform it how much more capacity can this collector hold
                    max_additional_capacity = self.agent.collector_capacity - self.agent.current_occupancy
                    # create the data json
                    data = {
                        "collector_jid": str(self.agent.jid),
                        "max_additional_capacity": max_additional_capacity
                    }
                    # create the message with destination to the collection center / trash
                    msg = Message(to=next_location)
                    msg.set_metadata("performative", "collector_inform") # set the message metadata
                    msg.body = json.dumps(data)

                    await self.send(msg) # send msg to collection center / trash

                    # wait for the response of the trash/collection center
                    msg = await self.receive(timeout=5) # wait for the response for 5 seconds
                    if msg:
                        performative = msg.get_metadata("performative")
                        if performative == 'confirm_trash':
                            data = json.loads(msg.body)  # deserialize JSON back to a path
                            trash_to_dispose = data
                            self.agent.current_occupancy = min(self.agent.current_occupancy + trash_to_dispose, self.agent.collector_capacity)
                            print(f"{self.agent.name}: Current occupancy is now {self.agent.current_occupancy:.2f}")
                        elif performative == 'confirm_center':
                            # Collector is in the center, so the trash is disposed
                            print(f"{self.agent.name}: Received answer from center, disposing trash")
                            self.agent.current_occupancy = 0
                        else:
                            print("Agent {}:".format(str(self.agent.name)) + f" Message not understood! Performative - {performative}")
            elif performative == 'confirm_trash':
                trash_to_dispose = data
                self.agent.current_occupancy = min(self.agent.current_occupancy + trash_to_dispose, self.agent.collector_capacity)
            elif performative == 'cfp':
                # proposal request
                locations_map = self.agent.locations_map # get the map with the paths information
                # convert the dictionary's keys to integer, because json.dumps convert int keys to string
                trash_occupancies_dict = {int(k): v for k, v in data["trash_occupancies_dict"].items()}
                best_path, _, routes, rating = self.agent.get_best_path_rating(locations_map, trash_occupancies_dict)
                # send proposal to the center agent
                # the proposal contains the best path for this collector, along with the path's rating
                msg = Message(to=self.get('center_jid'))
                msg.set_metadata("performative", "propose") # set the message metadata
                data = {
                    "collector_jid": str(self.agent.jid),
                    "best_path": best_path,
                    "routes": routes,
                    "rating": rating,
                }
                msg.body = json.dumps(data)
                await self.send(msg) # send msg to collection center / trash

            else:
                print("Agent {}:".format(str(self.agent.name)) + " Message not understood!")
