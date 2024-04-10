import jsonpickle
from spade.message import Message
from spade.behaviour import PeriodicBehaviour

# Behaviour that let's a Manager know when a Trash agent is full.

class TrashFull(PeriodicBehaviour):
    async def run(self):
        print("Trash is full!")

        msg = Message(to=self.agent.manager_jid)          # Instantiate the message (The manager_jid has to be set)
        msg.set_metadata("performative", "REQUEST")       # Set the "inform" FIPA performative
        msg.body = jsonpickle.encode(self.agent.location) # Sends the location of the Agent in the body of the message

        await self.send(msg)


