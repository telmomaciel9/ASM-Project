from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json
import asyncio
from util import jid_to_name

class CollectTrash_Behav(OneShotBehaviour):
    def __init__(self, path, routes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path
        self.routes = routes

    async def on_start(self):
        self.collection_center_pos = self.agent.jid_to_position_dict[self.get("center_jid")]

    async def run(self):
        if len(self.path) > 0 and self.path[0] == str(self.get('center_jid')):
            # if the first location is the collection center, remove this from the path (because the trash collector starts there)
            self.path.pop(0)
        path_route = list(zip(self.path, self.routes))
        for next_location, route in path_route:
            if not await self.go_to_location(next_location, route):
                # go_to_location returns false, so the collector is going early to collection center
                break

    """
    Sends a message to the next location with the remaining capacity of this collector
    """
    async def inform_next_location(self, next_location):
        # now that we are at the next agent's location, we inform it how much more capacity can this collector hold
        max_additional_capacity = self.agent.collector_capacity - self.agent.current_occupancy
        # create the data json
        data = {
            "max_additional_capacity": max_additional_capacity
        }
        # create the message with destination to the collection center / trash
        msg = Message(to=next_location)
        msg.set_metadata("performative", "collector_inform") # set the message metadata
        msg.body = json.dumps(data)
        await self.send(msg) # send msg to collection center / trash

    """
    Handles the confirm message from the trash agent
    Gets the amount of trash to dispose and updates the current occupancy
    """
    async def handle_confirm_trash(self, data, sender_jid):
        print(f"{self.agent.name}: Received confirm from {jid_to_name(sender_jid)}, collecting trash")
        trash_to_dispose = data
        self.agent.current_occupancy = min(self.agent.current_occupancy + trash_to_dispose, self.agent.collector_capacity)
        await self.inform_capacity_to_center(sender_jid)

    """
    Handles the confirm message from the center agent
    Resets capacity and informs the new capacity to the center
    """
    async def handle_confirm_center(self, sender_jid):
        # Collector is in the center, so the trash is disposed
        print(f"{self.agent.name}: Received confirm from center, disposing trash")
        self.agent.current_occupancy = 0
        await self.inform_capacity_to_center(sender_jid)

    """
    Sends a message to the next location with the remaining capacity of this collector
    """
    async def inform_capacity_to_center(self, sender_jid):
        # read current occupancy of the trash
        remaining_capacity = self.agent.collector_capacity - self.agent.current_occupancy

        # inform capacity to the central
        msg = Message(to=self.get('center_jid'))
        data = {
            "remaining_capacity": remaining_capacity,
            "current_location": sender_jid,
        }
        msg.body = json.dumps(data)
        msg.set_metadata("performative", "inform_collector_capacity") # set the message inform

        await self.send(msg) # send msg to collection center

    """
    This function receives a location and a route to that location, and waits for the collector to reach that location
    After the collector reaches that location, it communicates with the agent (can be trash or center), and collects/disposes the trash
    If it reaches max occupancy, it goes earlier to the CollectionCenter

    Returns False if it goes early to collection center, True otherwise
    """
    async def go_to_location(self, location, route):
        # go to next_location
        print("{}: Going to {}".format(self.agent.name, jid_to_name(location)))
        # destination position is the position of the collection center agent
        destination_pos = self.agent.jid_to_position_dict[location]
        self.agent.go_to_position(route)
        while self.agent.position != destination_pos:
            await asyncio.sleep(0.1)  # Use asyncio.sleep instead of time.sleep
        await self.inform_next_location(location)

        # wait for the reply of the next location
        msg_reply = await self.receive(timeout=5) # wait for a message for 5 seconds
        sender_jid = str(msg_reply.sender)
        performative = msg_reply.get_metadata("performative")
        if msg_reply.body:
            data = json.loads(msg_reply.body)  # deserialize JSON back to a path
        else:
            data = None
        if performative == "confirm_trash":
            await self.handle_confirm_trash(data, sender_jid)
        elif performative == "confirm_center":
            await self.handle_confirm_center(sender_jid)
        else:
            print(f"{self.agent.name}: Didn't receive confirm of {jid_to_name(location)}")

        # check if collector is full
        if self.agent.current_occupancy >= self.agent.collector_capacity and self.agent.position != self.collection_center_pos:
            print("{}: Reached max occupancy.".format(self.agent.name))
            route_to_central = self.agent.get_route_to_central(location)
            await self.go_to_location(self.get("center_jid"), route_to_central)
            return False
        else:
            return True