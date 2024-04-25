"""
Trash Collector agent Behaviour 
This behaviour is responsible for receiving trash collection order from the central (in the form of a message containing a Path), and collecting the trash
This behaviour is also responsible for receiving the amount of trash to dispose from the Trash agents, and "disposing" it
"""

from spade.message import Message
from spade.behaviour import CyclicBehaviour

import time
import asyncio  # Import asyncio for asyncio.sleep
import json

class ReceivePath_Behav(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=10) # wait for a message for 10 seconds
        
        if msg:
            # Message Threatment based on different ACLMessage performatives
            performative = msg.get_metadata("performative")
            if performative == 'collect_trash': # Handle request to go collect trash in a path
                data = json.loads(msg.body)  # deserialize JSON back to a path
                path = data["path"]
                cost = data["cost"]
                routes = data["routes"]

                if path[0] == str(self.get('center_jid')):
                    # if the first location is the collection center, remove this from the path (because the trash collector starts there)
                    path.pop(0)

                # we zip path from the 1st index because the 0th index is the start location.
                # The trash collector is already in the start location therefore we skip that
                path_cost_route = list(zip(path, cost, routes))

                for next_location, cost, route in path_cost_route:
                    # go to next_location
                    # sleep for 'cost'
                    print("Collector: Going to {}, cost is {:.7f}".format(next_location, cost))
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
                        if performative == 'dispose_trash':
                            data = json.loads(msg.body)  # deserialize JSON back to a path
                            trash_to_dispose = data
                            self.agent.current_occupancy = min(self.agent.current_occupancy + trash_to_dispose, self.agent.collector_capacity)
                            print(f"Collector: Current occupancy is now {self.agent.current_occupancy}")
                        elif performative == 'answer_center':
                            # Collector is in the center, so the trash is disposed
                            print(f"Collector: Received answer from center, disposing trash")
                            self.agent.current_occupancy = 0
                        else:
                            print("Agent {}:".format(str(self.agent.name)) + f" Message not understood! Performative - {performative}")
                    


                # collector has returned to the collection center. Inform the center?
            elif performative == 'dispose_trash':
                data = json.loads(msg.body)  # deserialize JSON back to a path
                trash_to_dispose = data
                self.agent.current_occupancy = min(self.agent.current_occupancy + trash_to_dispose, self.agent.collector_capacity)
            else:
                print("Agent {}:".format(str(self.agent.name)) + " Message not understood!")