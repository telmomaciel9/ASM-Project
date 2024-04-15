from spade import agent
from Behaviours.Collector.receivePath_Behav import ReceivePath_Behav

class TrashCollector(agent.Agent):

    collector_capacity = 1000
    current_occupancy = 0

    async def setup(self):
        print("Trash Collector Agent {}".format(str(self.jid)) + " starting...")
        
        self.collector_capacity = 1000 # max collector capacity
        self.current_occupancy = 0 # current occupancy of the collector (max is collector_capacity)

        a = ReceivePath_Behav()
        #b = DisposeTrash_Behav()

        self.add_behaviour(a)
        #self.add_behaviour(b)