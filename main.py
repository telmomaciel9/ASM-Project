from spade import quit_spade
import time 
from maps import GraphMap
import asyncio

from Agents.center import CollectionCenter
from Agents.collector import TrashCollector
from Agents.trash import Trash

XMPP_SERVER = 'ubuntu.myguest.virtualbox.org' #put your XMPP_SERVER
PASSWORD = 'NOPASSWORD' #put your password

if __name__ == '__main__':

    # this variable represents the number of trashes in the simulation
    n_trashes = 4
    # this variable represents the number of trash collectors in the simulation
    n_collectors = 2

    # creates the jids for the trash agents
    trash_jids = [f'trash{i}@'+XMPP_SERVER for i in range(n_trashes)]
    # creates the jids for the trash collector agents
    collector_jids = [f'collector{i}@'+XMPP_SERVER for i in range(n_collectors)]
    # create the jid of the collection center
    center_jid = "center@"+XMPP_SERVER

    # create Collection Center agent
    center_agent = CollectionCenter(center_jid, PASSWORD)
    # create Trash agents
    trash_agents = [Trash(jid, PASSWORD) for jid in trash_jids]
    # create Trash Collector agents
    collector_agents = [TrashCollector(jid, PASSWORD) for jid in collector_jids]
    # associate the trash collector agents to the collection center agent
    center_agent.set_collectors(collector_agents)
    map1 = GraphMap(trash_agents, center_agent)
        
    center_agent.set('map', map1) # set the map of trash agents and central
    future = center_agent.start() # Execute collection center agent
    future.result()

    # execute trash agents
    for trash_agent in trash_agents:
        trash_agent.set('center_jid', center_jid)
        future = trash_agent.start()
        future.result()
        # trash_agent.web.start(hostname="127.0.0.1", port=10000)

    # execute trash collector agents
    for collector_agent in collector_agents:
        collector_agent.set('center_jid', center_jid)
        future = collector_agent.start()
        future.result()


    while center_agent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            (agent.stop() for agent in trash_agents)
            (agent.stop() for agent in collector_agents)
            center_agent.stop()
            break
    print('Agents finished')
    # finish all the agents and behaviors running in your process
    quit_spade()