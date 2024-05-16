import random
import json
from datetime import datetime

from spade.behaviour import PeriodicBehaviour
from spade.message import Message

from config import Config

"""
Trash Agent behaviour
This behaviour is responsible for:
- periodically informing the collection center about this agent's occupancy
"""

class InformCapacity_Behav (PeriodicBehaviour):
    async def run(self):

        # read current occupancy of the trash
        current_occupancy = self.agent.current_occupancy

        # Calculate the number of seconds since the trash was last collected
        current_time = datetime.now()
        last_gathered_time = self.agent.last_gathered_time
        elapsed_time_seconds = (current_time - last_gathered_time).total_seconds()

        # inform capacity to the central
        msg = Message(to=self.get('center_jid'))
        data = {
            "current_occupancy": current_occupancy,
            "elapsed_time_seconds": elapsed_time_seconds
        }
        msg.body = json.dumps(data)
        msg.set_metadata("performative", "inform_trash_occupancy") # set the message inform

        await self.send(msg) # send msg to collection center

        # increment current occupancy (for the sake of the simulation)
        trash_to_increase = Config().trash_occupancy_per_simulation_second
        # the trash capacity cant exceed the maximum capacity. That's why we do a 'min'
        self.agent.current_occupancy = min(current_occupancy + trash_to_increase, self.agent.trash_capacity) # update current occupancy of the trash