from spade import agent

from Behaviours.Trash.informCapacity_Behav import InformCapacity_Behav
from Behaviours.Trash.disposeTrash_Behav import DisposeTrash_Behav

class Trash(agent.Agent):

    trash_capacity = 100
    current_occupancy = 0

    async def setup(self):
        print("Trash Agent '{}'".format(str(self.jid)) + " starting...")

        self.trash_capacity = 100 # max trash capacity
        self.current_occupancy = 0 # current occupancy of the trash (max is trash_capacity)
        
        if self.get("position"):
            self.position = self.get("position")
        else:
            print(f"Trash Agent {self.jid}: position not defined!")

        a = InformCapacity_Behav(period = 1)
        b = DisposeTrash_Behav()

        self.add_behaviour(a)
        self.add_behaviour(b)