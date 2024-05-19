"""
Trash Collector agent Behaviour 
This behaviour is responsible for receiving trash collection order from the central (in the form of a message containing a Path), and collecting the trash
This behaviour is also responsible for receiving the amount of trash to dispose from the Trash agents, and "disposing" it
"""

from spade.message import Message
from spade.behaviour import CyclicBehaviour
from spade.template import Template

from Behaviours.Collector.collectTrash_Behav import CollectTrash_Behav

from logs import log_collector
from util import jid_to_name
import time
import asyncio  # Import asyncio for asyncio.sleep
import json

class ReceiveMessages_Behav(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=10) # wait for a message for 10 seconds
        
        if msg:
            # Message Threatment based on different ACLMessage performatives
            sender_jid = str(msg.sender)
            performative = msg.get_metadata("performative")
            data = None
            if msg.body:
                data = json.loads(msg.body)  # deserialize JSON back to a path
            if performative == 'accept-proposal': # Handle request to go collect trash in a path
                await self.handle_accept_proposal(data)
            elif performative == 'cfp':
                await self.handle_cfp(data)
            else:
                log_collector(str(self.agent.jid), "Message not understood!")

    async def handle_accept_proposal(self, data):
        path = data["path"]
        routes = data["routes"]
        log_collector(str(self.agent.jid), f"Accepted proposal. Path is {path}")

        # increase the number of trips done by this collector
        self.agent.n_trips += 1

        # Create and add the one-shot behavior for collecting trash
        collect_trash_behaviour = CollectTrash_Behav(path, routes)
        # create the templates with the performatives that this behaviour receives only
        template1 = Template(metadata={"performative": "confirm_trash"})
        template2 = Template(metadata={"performative": "confirm_center"})
        # we add an OR of the templates because the behaviour can receive any of the messages
        self.agent.add_behaviour(collect_trash_behaviour, template1 | template2)

    async def handle_cfp(self, data):
        # proposal request
        trash_occupancies_dict = data["trash_occupancies_dict"]
        best_path = data["best_path"]
        routes = data["routes"]
        rating = self.agent.calculate_rating(sum(list(trash_occupancies_dict.values())))

        total_occupancy = 0
        truncated_path = [best_path[0]]
        for node in best_path[1:-1]:
            truncated_path.append(node)
            total_occupancy += trash_occupancies_dict[node]
            if total_occupancy > self.agent.collector_capacity:
                break
        truncated_path.append(best_path[-1])

        # send proposal to the center agent
        # the proposal contains the best path and routes for this collector, along with the path's rating
        msg = Message(to=self.get('center_jid'))
        msg.set_metadata("performative", "propose") # set the message metadata
        data = {
            "best_path": truncated_path,
            "routes": routes,
            "rating": rating,
        }
        msg.body = json.dumps(data)
        await self.send(msg) # send msg to collection center / trash