import pymysql, pymysql.cursors, os, uuid, copy, csv, requests

from dotenv import load_dotenv


crewModel = {
    'id': '',
    'email': '',
    'name': '',
    'cities': []
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
        url = os.getenv('POOL3_URL')
        if url == None:
            url = "http://pool-api.localhost"
        token = os.getenv('POOL3_KEY')
        if token == None:
            token = "secret"
        headers = {"Content-Type": "application/json" ,"Authorization": "Bearer " + token}
        for entry in crew_list:
            response = requests.post(url + '/crews/migrate', headers=headers, json=entry)
            print(response.text)
        
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
