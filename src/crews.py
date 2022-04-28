import pymysql, pymysql.cursors, os, uuid, copy, csv

from dotenv import load_dotenv


crewModel = {
    'id': '',
    'email': '',
    'name': '',
}

class Crews:
    
    def __init__(self) -> None:
        load_dotenv()
        password=os.getenv('DROPS_PASSWORD')
        port_string= os.getenv("DROPS_PORT")
        if port_string != None:
            port = int(port_string)
        else:
            port = 3306
        if password == None:
            print("set")
            exit(1)
        self.connection = pymysql.connect(
                host=os.getenv('DROPS_HOST'),
                port=port,
                user=os.getenv('DROPS_USER'),
                password=password,
                database="drops",
                cursorclass=pymysql.cursors.DictCursor
                )
        password=os.getenv('POOL1_PASSWORD')
        if password == None:
            print("set pool1 pw")
            exit(1)
        self.pool1 = pymysql.connect(
                host=os.getenv('POOL1_HOST'),
                port=port,
                user=os.getenv('POOL1_USER'),
                password=password,
                database="db175370026",
                cursorclass=pymysql.cursors.DictCursor
                )
    
    def migrate(self, file):
        crew_list = self.convert_csv(file)
        crew_list = self.get_uuid(crew_list)
        for entry in crew_list:
            print(entry)
#        sql = ('select * from Crew')
#        with self.connection.cursor() as cursor:
#            cursor.execute(sql)
#            result = cursor.fetchall()
#        for entry in result:
#            print(uuid.UUID(bytes=entry['publicId']))
#            with self.pool1.cursor() as cursor:
#                sql = ('select * from wp_users where user_login = %s')
#                cursor.execute(sql, entry["name"])
#                wp_user = cursor.fetchone()
#                email = ''
#                if wp_user != None:
#                    email = wp_user['user_email']
#                crew = copy.deepcopy(crewModel)
#                crew['id'] = str(uuid.UUID(bytes=entry['publicId']))
#                crew['name'] = entry["name"]
#                crew['email'] = email
#                print(crew)

    def get_uuid(self, crew_list):
        sql = ('select * from Crew where name = %s')
        for entry in crew_list:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, entry["name"])
                result = cursor.fetchone()
                if result != None:
                    entry['id'] = str(uuid.UUID(bytes=result['publicId']))
        return crew_list


    def convert_csv(self, file):
        result = []
        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            line_count = 0
            for row in csv_reader:
                # break at end of file
                if row[0] == None:
                    break
                if line_count == 0:
                    line_count += 1
                else:
                    crew = copy.deepcopy(crewModel)
                    crew['name'] = row[0][9:]
                    crew['email'] = row[1]
                    result.append(crew)
                    line_count += 1
        return result


    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "migrate":
            self.migrate(argv[3])
