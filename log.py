from colorama import Fore, Style, init
import datetime

class Log:

    def __init__(self, agent):
        init(autoreset=True)

        self.timestamp_color = Fore.BLUE

        if agent == "center":
            self.color = Fore.GREEN
            self.agent = "Center"
        elif agent == "collector":
            self.color = Fore.RED
            self.agent = "Collector"
        elif agent == "trash":
            self.color = Fore.YELLOW
            self.agent = "Trash"
        else:
            self.color = None


    def log(self, text):
        timestamp = datetime.datetime.now()
        print(self.timestamp_color + "[" + timestamp.strftime('%H:%M:%S') + "] ", end="")

        if self.color != None:
            print(self.color + self.agent + ": ", end="")
            print(text)
        else: 
            print(text)