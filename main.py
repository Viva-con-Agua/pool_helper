# Helper scripts for pool 1/2 processes
import sys
from src.profile import ProfileHandler
from src.address import AddressHandler
from src.newsletter import NewsletterHandler
from src.event_stats import EventStats
from src.asps import Asps
from src.crews import Crews
from src.user import UserHandler
from src.user_crew import UserCrewHandler
def help_asp():
    print("Commands for asp: all, get")
    print("  all")
    print("  get")

def help_prog():
    print("Commands: \n   asp")

def main(argv):
    if len(argv) < 1:
        help_prog()
    if argv[1] == "asp":
        prog = Asps()
        prog.process(argv)
    elif argv[1] == "crews":
        prog = Crews()
        prog.process(argv)
    elif argv[1] == "users":
        prog = UserHandler()
        prog.process(argv)
    elif argv[1] == "event":
        prog = EventStats()
        prog.process(argv)
    elif argv[1] == "newsletter":
        prog = NewsletterHandler()
        prog.process(argv)
    elif argv[1] == "address":
        prog = AddressHandler()
        prog.process(argv)
    elif argv[1] == "profile":
        prog = ProfileHandler()
        prog.process(argv)
    elif argv[1] == "user_crew":
        prog = UserCrewHandler()
        prog.process(argv)



if __name__ == "__main__":
    main(sys.argv)


