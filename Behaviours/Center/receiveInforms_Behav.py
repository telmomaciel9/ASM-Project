from spade.message import Message
from spade.behaviour import CyclicBehaviour

import json

"""
Collection Center Agent Behaviour
This behaviour is responsible for receiving messages from trashes and from trash collectors (garbage trucks).
The messages received from Trash agents are informative of how much trash each agent has
The messages received from Trash Collector agents are informative that the collector has returned to the center
"""

class ReceiveInforms_Behav(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=10) # wait for a message for 10 seconds

        if msg:
            # Message Threatment based on different ACLMessage performatives
            performative = msg.get_metadata("performative")
            if performative == 'inform': # Handle trash occupancy inform
                data = json.loads(msg.body)  # deserialize JSON back to a Python dictionary
                trash_name = data["name"]
                occupancy = data["current_occupancy"]
                self.agent.trash_occupancies[trash_name] = int(occupancy)
                
                print("Center: Trash {} has current occupancy {}".format(trash_name, occupancy))

                total_occupancy_threshold = 100
                # If the trash occupancy of all trashes combined subtracted by the total capacity of collectors on the road excedes the threshold, we send a collector
                if (sum(list(self.agent.trash_occupancies.values())) - self.agent.get_collector_capacity_on_the_road()) > 100 and self.agent.get_number_of_available_collectors() >= 0:
                    # calculate path for the trash collector to follow to pick up a lot of trash and in a short distance
                    available_collector_jid = self.agent.get_available_collector_jid()
                    if available_collector_jid is not None:
                        # set the trash collector availability to False, because it is going to be used for the next collection
                        self.agent.set_collector_availability(available_collector_jid,False)
                        # get the best path from the central to the trashes and back
                        path, cost = self.agent.get_best_path()
                        data = {
                            "path": path,
                            "cost": cost
                        }
                        # create the message with destination to the trash collector
                        msg = Message(to=available_collector_jid)
                        # the body of the message contains only the path of the trash collector
                        msg.body = json.dumps(data)
                        msg.set_metadata("performative", "collect_trash") # set the message metadata

                        await self.send(msg) # send msg to collection center
                    else:
                        print("There are no available trash collectors!")
            elif performative == 'collector_inform':
                data = json.loads(msg.body)  # deserialize JSON back to a Python dictionary
                collector_jid = data["collector_jid"]
                print(f"Center: {collector_jid} has returned to the Collection Center!")
                # this trash collector has returned, so we set its availability to True
                self.agent.set_collector_availability(collector_jid, True)
            else:
                print("Agent {}:".format(str(self.agent.name)) + " Message not understood!")
        else:
            print("Agent {}:".format(str(self.agent.name)) + "Did not received any message after 10 seconds")