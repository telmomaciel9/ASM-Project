from spade.message import Message
from spade.behaviour import CyclicBehaviour
from util import jid_to_name
import json

"""
Trash Agent behaviour
This behaviour is responsible for:
- receiving messages from the trash collector agents, disposing the trash to them
"""

class DisposeTrash_Behav(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=10) # wait for a message for 10 seconds

        if msg:
            collector_jid = str(msg.sender)
            # Message Threatment based on different ACLMessage performatives
            performative = msg.get_metadata("performative")
            if performative == 'collector_inform': # Handle trash collector inform
                data = json.loads(msg.body)
                max_additional_capacity = data["max_additional_capacity"]
                trash_to_dispose = min(max_additional_capacity, self.agent.current_occupancy)
                print(f"{self.agent.name}: Disposing {trash_to_dispose:.2f}kg to {jid_to_name(collector_jid)}")

                # deduct the trash to dispose from the current trash occupancy
                self.agent.current_occupancy -= trash_to_dispose

                # create message to be sent to the trash collector
                msg = Message(to=collector_jid)
                msg.set_metadata("performative", "confirm_trash") # set the message metadata
                # the only information we need to transmit is the amount of trash to dispose
                data = trash_to_dispose
                # convert the data into json
                msg.body = json.dumps(data)

                await self.send(msg) # send message to the trash collector