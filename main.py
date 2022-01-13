# Helper scripts for pool 1/2 processes
import sys, getopt
from src.asps import Asps

def help_asp():
    print("Commands for asp: all, get")
    print("  all")
    print("  get")

def help_prog():
    print("Commands: \n   asp")

def main(argv):
    if len(argv) < 1:
        help_prog()
    prog = argv[1]
    if prog == "asp":
        asps = Asps()
        func = argv[2]
        if func == "all":
            options = "hc:"
            long = ["help", "crew"]
            crew  = None 
            try:
                a, _ = getopt.getopt(argv[3:], options, long)
                for ca, cv in a:
                    if cv in ("-h", "--help"):
                        print("help")
                    elif ca in ("-c", "--crew"):
                        crew = cv
            except getopt.error as err:
                # output error, and return with an error code
                print (str(err))
            asps.all(crew)
        elif func == "get":
            options = "he:c:"
            long = ["help", "email", "crew"]
            crew  = None 
            email = None
            try:
                a, _ = getopt.getopt(argv[3:], options, long)
                for ca, cv in a:
                    if cv in ("-h", "--help"):
                        print("help")
                    elif ca in ("-e", "--email"):
                        email = cv
                    elif ca in ("-c", "--crew"):
                        crew = cv
            except getopt.error as err:
                # output error, and return with an error code
                print (str(err))
            asps.get(email, crew)
        elif func == "set":
            options = "he:c:p:l:"
            long = ["help", "email=", "crew=", "pillar=", "list="]
            crew  = None 
            email = None
            pillar = None
            csv = None
            try:
                a, _ = getopt.getopt(argv[3:], options, long)
                for ca, cv in a:
                    if cv in ("-h", "--help"):
                        print("help")
                    elif ca in ("-e", "--email"):
                        email = cv
                    elif ca in ("-c", "--crew"):
                        crew = cv
                    elif ca in ("-l", "--list"):
                        csv = cv
                    elif ca in ("-p", "--pillar"):
                        pillar = cv

            except getopt.error as err:
                # output error, and return with an error code
                print (str(err))
            if csv != None:
                asps.set_list(csv)
                exit(0)
            asps.set(email, crew, pillar)
        elif func == "delete":
            options = "he:c:"
            long = ["help", "email", "crew"]
            crew  = None 
            email = None
            try:
                a, _ = getopt.getopt(argv[3:], options, long)
                for ca, cv in a:
                    if cv in ("-h", "--help"):
                        print("help")
                    elif ca in ("-e", "--email"):
                        email = cv
                    elif ca in ("-c", "--crew"):
                        crew = cv
            except getopt.error as err:
                # output error, and return with an error code
                print (str(err))
            if email != None and crew != None:
                print("-e takes no effect in with -c")
            elif crew != None: 
                asps.delete_for_crew(crew)
                exit(0)
            elif email != None:
                asps.delete(email)
                exit(0)
            else:
                print("error")
                exit(1)

if __name__ == "__main__":
    main(sys.argv)


