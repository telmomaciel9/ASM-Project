
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
from spade.template import Template

import asyncio
import json
from util import jid_to_name

from Behaviours.Center.receiveProposals_Behav import ReceiveProposals_Behav

# total trash occupancy threshold
total_occupancy_threshold = 100

class ProposeCollectors_Behav(PeriodicBehaviour):
    async def run(self):

        total_occupancy_threshold = self.get('threshold') # get the threshold variable and set the occupancy threshold

        # If the trash occupancy of all trashes combined subtracted by the total capacity of collectors on the road excedes the threshold, we send a collector
        if (sum(list(self.agent.trash_occupancies.values())) - self.agent.get_collector_capacity_on_the_road()) > total_occupancy_threshold and self.agent.get_number_of_available_collectors() >= 0:
            # get the jids of the available collectors
            available_collectors_jids = self.agent.get_available_collectors_jids()
            num_available_collectors = len(available_collectors_jids)

            # Create and add the one-shot behavior for receiving proposals
            receive_proposals_behaviour = ReceiveProposals_Behav(num_available_collectors)
            # set a template in the one shot behaviour so that it can only receive messages with performative equals to "propose"
            template = Template(metadata={"performative": "propose"})
            self.agent.add_behaviour(receive_proposals_behaviour, template)

            for collector_jid in available_collectors_jids:
                # for each collector, issue a call for proposals
                msg = Message(to=collector_jid)
                # issue a call for proposals. Center requests proposals from the collectors, to get the best proposal
                msg.set_metadata("performative", "cfp")
                excluded_locations = self.agent.get_excluded_paths()
                data = {
                    "trash_occupancies_dict": self.agent.trash_occupancies,
                    "excluded_locations": excluded_locations,
                }
                msg.body = json.dumps(data)
                await self.send(msg)