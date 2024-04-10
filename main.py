import spade
import time
from Agents.Manager import Manager
from Agents.Trash import Trash

# Manager
manager = Manager("Manager@183sawyer", "NOPASSWORD")
future = manager.start()
future.result()

# Trash agent
trash_agent = Trash("Trash_Agent1@183sawyer", "NOPASSWORD")
trash_agent.setManagerJID("Manager")
future = trash_agent.start()
future.result()

time.sleep(20)