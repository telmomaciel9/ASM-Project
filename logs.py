# logger.py

from colorama import Fore, Style, init

from util import jid_to_name

# Initialize colorama
init(autoreset=True)

def log_center(jid, message):
    print(f"{Fore.GREEN}{jid_to_name(jid)}: {Style.RESET_ALL}{message}")

def log_collector(jid, message):
    print(f"{Fore.BLUE}{jid_to_name(jid)}: {Style.RESET_ALL}{message}")

def log_trash(jid, message):
    print(f"{Fore.RED}{jid_to_name(jid)}: {Style.RESET_ALL}{message}")

# Example usage
if __name__ == "__main__":
    log_center("position not defined!")
    log_collector("Collector is full!")
    log_trash("Trash is at full capacity!")
