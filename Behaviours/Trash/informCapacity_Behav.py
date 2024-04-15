import random
import json

from spade.behaviour import PeriodicBehaviour
from spade.message import Message

"""
Trash Agent behaviour
This behaviour is responsible for:
- periodically informing the collection center about this agent's occupancy
"""

class InformCapacity_Behav (PeriodicBehaviour):
    async def run(self):

        # read current occupancy of the trash
        current_occupancy = self.agent.current_occupancy

        # inform capacity to the central
        msg = Message(to=self.get('center_jid'))
        data = {
            "name": self.agent.name,
            "current_occupancy": current_occupancy
        }
        msg.body = json.dumps(data)
        msg.set_metadata("performative", "inform") # set the message inform

        await self.send(msg) # send msg to collection center

        # increment current occupancy (for the sake of the simulation)
        random_num = random.randint(0,5) # generate between 0 and 5 trash
        # the trash capacity cant exceed the maximum capacity. That's why we do a 'min'
        self.agent.current_occupancy = min(current_occupancy + random_num, self.agent.trash_capacity) # update current occupancy of the trash