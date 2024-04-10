import random
import datetime
from spade import agent
from Shared.Position import Position
from Behaviours.TrashFull import TrashFull

class Trash(agent.Agent):
    
    async def setup(self):
        self.full = False
        self.location = Position(random.randint(0, 101), random.randint(0, 101))

        start_at = datetime.datetime.now() + datetime.timedelta(seconds=3) # When to start the behaviour
        self.add_behaviour(TrashFull(period=10, start_at=start_at))

    def setManagerJID(self, JID):
        self.manger_jid = JID