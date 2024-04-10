from spade.behaviour import CyclicBehaviour

class Listen(CyclicBehaviour):
    async def run(self):
        print("Listening to messages!")

        msg = await self.receive(timeout=5) # wait for 5 seconds to receive a message
        if msg:
            print("Message received with content: {}".format(msg.body))
        else:
            print("No message received!")
        
    async def on_end(self):
        self.agent.stop()