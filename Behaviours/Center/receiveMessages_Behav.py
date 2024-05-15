from spade.message import Message
from spade.behaviour import CyclicBehaviour

import asyncio
import json
from util import jid_to_name


"""
Collection Center Agent Behaviour
This behaviour is responsible for receiving messages from trashes and from trash collectors (garbage trucks).
The messages received from Trash agents are informative of how much trash each agent has
The messages received from Trash Collector agents are informative that the collector has returned to the center
"""

class ReceiveMessages_Behav(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=10) # wait for a message for 10 seconds

        if msg:
            sender_jid = str(msg.sender)
            # Message Threatment based on different ACLMessage performatives
            performative = msg.get_metadata("performative")
            data = json.loads(msg.body)  # deserialize JSON back to a Python dictionary
            if performative == 'inform': # Handle trash occupancy inform
                await self.handle_inform_trash_occupancy(data, sender_jid)
            elif performative == 'collector_inform':
                await self.handle_collector_inform(sender_jid)
            elif performative == 'propose':
                await self.handle_propose(data, sender_jid)
            else:
                print("Agent {}:".format(str(self.agent.name)) + " Message not understood!")
        else:
            print("Agent {}:".format(str(self.agent.name)) + "Did not received any message after 10 seconds")

    async def handle_inform_trash_occupancy(self, data, trash_jid):
        occupancy = data["current_occupancy"]
        self.agent.trash_occupancies[trash_jid] = occupancy

    async def handle_collector_inform(self, collector_jid):
        print(f"Center: {jid_to_name(collector_jid)} has returned to the Collection Center!")
        # this trash collector has returned, so we set its availability to True
        self.agent.set_collector_availability(collector_jid, True)
        # setup answer message to trash collector agent
        send_msg = Message(to=collector_jid)
        # the body of the message contains only the path of the trash collector
        #msg.body = json.dumps(json.dumps({})) # empty message
        send_msg.set_metadata("performative", "confirm_center") # set the message metadata
        await self.send(send_msg) # send message to collector

    async def handle_propose(self, data, collector_jid):
        # received path and rating proposal from collector agent
        best_path = data["best_path"]
        routes = data["routes"]
        rating = data["rating"]
        self.agent.collector_proposals[collector_jid] = (rating, best_path, routes)
        print(f"Center: Received proposal from {collector_jid}")