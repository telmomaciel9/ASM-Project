import datetime
from spade import agent
from Behaviours.Listen import Listen

class Manager(agent.Agent):

    async def setup(self):
        self.add_behaviour(Listen())
    

        
