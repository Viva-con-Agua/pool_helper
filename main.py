# Helper scripts for pool 1/2 processes
import sys
from src.asps import Asps
from src.crews import Crews
from src.user import User
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
        prog = User()
        prog.process(argv)
if __name__ == "__main__":
    main(sys.argv)


