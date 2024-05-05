from spade import quit_spade
import time 
from Classes.maps import GraphMap
import asyncio
from util import update_interval
import json

from Agents.center import CollectionCenter
from Agents.collector import TrashCollector
from Agents.trash import Trash
from Classes.Position import Position
from Classes.simulation import Simulator

from config import Config

XMPP_SERVER = 'ubuntu.myguest.virtualbox.org' # XMPP_SERVER
PASSWORD = 'NOPASSWORD' # password

simulation_update_interval = 0.02

if __name__ == '__main__':

    config_path = 'config/config1.json'  # The path to your configuration file
    config = Config(config_path)

    # this variable represents the number of trash collectors in the simulation
    n_collectors = config.n_collectors
    # this variable represents the number of trashes in the simulation
    n_trashes = config.n_trashes
    # get position objects of the agents
    center_position = Position(*config.center_position)
    trash_positions = [Position(*pos) for pos in config.trash_positions]

    jump_size = config.get_jump_size  # Use this variable where needed in your code
    update_interval = config.get_update_interval  # Update your time.sleep calls with this variable
    images_directory = config.images_directory

    map_image_file = f'{images_directory}/map_image.png'
    truck_image_file = f'{images_directory}/truck_icon.png'
    trash_image_file = f'{images_directory}/trash_icon.png'

    # creates the jids for the trash agents
    trash_jids = [f'trash{i}@'+XMPP_SERVER for i in range(n_trashes)]
    # creates the jids for the trash collector agents
    collector_jids = [f'collector{i}@'+XMPP_SERVER for i in range(n_collectors)]
    # create the jid of the collection center
    center_jid = "center@"+XMPP_SERVER

    jids_to_position_dict = {agent_jid:pos for agent_jid,pos in zip(trash_jids + [center_jid], trash_positions + [center_position])}

    # create Collection Center agent
    center_agent = CollectionCenter(center_jid, PASSWORD)
    # create Trash agents
    trash_agents = []
    for i, jid in enumerate(trash_jids):
        trash_agent = Trash(jid, PASSWORD)
        trash_agent.set('center_jid', center_jid)
        trash_agent.set('id', i)
        trash_agent.set('position', trash_positions[i]) # set the position of the trash
        trash_agents.append(trash_agent)
    # create Trash Collector agents
    collector_agents = []
    for i, jid in enumerate(collector_jids):
        collector_agent = TrashCollector(jid, PASSWORD)
        collector_agent.set('center_jid', center_jid)
        collector_agent.set('position', center_position) # set the position of the agent to the center position (trash collectors start at the center)
        collector_agent.set('positions', jids_to_position_dict)
        collector_agents.append(collector_agent)

    # associate the trash collector agents to the collection center agent
    center_agent.set_collectors(collector_agents)
    center_agent.set('position', center_position) # set the map of trash agents and central

    # create entity that will visually simulate the interactions between the agents
    simulator = Simulator(map_image_file, truck_image_file, trash_image_file, n_collectors, n_trashes, center_position)
    # create the data structure that holds the information about the environment and the routes
    map1 = GraphMap(trash_agents, center_agent, simulator.G)

    center_agent.set_map(map1) # set the map of trash agents and central

    # start center agent
    future = center_agent.start(auto_register=True) # Execute collection center agent
    future.result() # wait for the agent to start

    # execute trash collector agents
    for collector_agent in collector_agents:
        future = collector_agent.start(auto_register=True) # start trash collector agent
        future.result() # wait for the agent to start

    # execute trash agents
    for i, trash_agent in enumerate(trash_agents):
        future = trash_agent.start(auto_register=True) # start the trash agent
        future.result() # wait for the agent to start


    while center_agent.is_alive():
        try:
            collector_positions = [collector.position for collector in collector_agents]
            trash_positions = [trash.position for trash in trash_agents]
            collector_occupancies = [collector.current_occupancy for collector in collector_agents]
            trash_occupancies = [trash.current_occupancy for trash in trash_agents]
            simulator.update_positions(collector_positions, trash_positions, collector_occupancies, trash_occupancies)
            time.sleep(simulation_update_interval)
        except KeyboardInterrupt:
            (agent.stop() for agent in trash_agents)
            (agent.stop() for agent in collector_agents)
            center_agent.stop()
            break
    print('Agents finished')
    # finish all the agents and behaviors running in your process
    quit_spade()