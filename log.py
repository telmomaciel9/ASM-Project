from colorama import Fore, Style, init
import datetime

class Log:

    def __init__(self, agent):
        init(autoreset=True)

        self.timestamp_color = Fore.BLUE
        
        if "center" in agent:
            self.color = Fore.GREEN
            self.agent = agent
        elif "collector" in agent:
            self.color = Fore.RED
            self.agent = agent
        elif "trash" in agent:
            self.color = Fore.YELLOW
            self.agent = agent
        else:
            self.color = None
            self.agent = None

    def log(self, text):
        timestamp = datetime.datetime.now()
        print(self.timestamp_color + "[" + timestamp.strftime('%H:%M:%S') + "] ", end="")

        if self.color != None:
            print(self.color + self.agent + ": ", end="")
            print(text)
        else: 
            print(text)