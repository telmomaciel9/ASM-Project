from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json
from util import jid_to_name

class ReceiveProposals_Behav(OneShotBehaviour):
    def __init__(self, num_available_collectors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_available_collectors = num_available_collectors
        self.received_proposals = 0
        self.proposals = {}


    async def run(self):
        print("num_collectors -", self.num_available_collectors)
        while self.received_proposals < self.num_available_collectors:
            msg = await self.receive(timeout=1)
            print("received proposal")
            if msg and msg.get_metadata("performative") == "propose":
                collector_jid = str(msg.sender)
                data = json.loads(msg.body)
                best_path = data["best_path"]
                routes = data["routes"]
                rating = data["rating"]
                self.proposals[collector_jid] = (rating, best_path, routes)
                self.received_proposals += 1
            else:
                break

        # Find the collector with the best rating
        if self.proposals:
            best_collector_jid, (best_rating, best_path, routes) = min(self.proposals.items(), key=lambda x: x[1][0])
            print(f"Center: Accepting proposal of {jid_to_name(best_collector_jid)}")
            await self.request_collector(best_collector_jid, best_path, routes)
        else:
            print("Center: No collectors have responded with a path.")

    """
    Given the jid of a collector, a path, and a route, request the collector to go on the specified path route
    """
    async def request_collector(self, collector_jid, path, routes):
        # set the trash collector availability to False, because it is going to be used for the next collection
        self.agent.set_collector_availability(collector_jid, False, path)
        # get the best path from the central to the trashes and back
        data = {
            "path": path,
            "routes": routes,
        }
        # create the message with destination to the trash collector
        msg = Message(to=collector_jid)
        # the body of the message contains only the path of the trash collector
        msg.body = json.dumps(data)
        msg.set_metadata("performative", "accept-proposal") # set the message metadata
        await self.send(msg) # send msg to trash collector