import pymysql, pymysql.cursors, os, uuid, copy, csv, requests

from tqdm import tqdm 
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
        self.api_key = os.getenv('GOOGLE_API_KEY')
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
        count = {
            'success': 0,
            'failed': 0,
            'error': []
        }
        headers = {"Content-Type": "application/json" ,"Authorization": "Bearer " + token}
        for i in tqdm (range (len(crew_list)), desc="Import Crews...", ncols=75):
            response = requests.post(url + '/crews/migrate', headers=headers, json=crew_list[i])
            if response.status_code != 201:
                count['failed'] = count['failed'] +1
                count['error'].append(response.text)
            else:
                count['success'] = count['success'] + 1
        print("Import Crews completed.")
        if len(count["error"]) != 0:
            print('Errors: ')
            for x in count['error']:
                print(x)
        print("Success: ", count['success'])
        print("Failed: ", count['failed'])

        
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
            count = sum(1 for _ in csv_reader)
            csv_file.seek(0)
            csv_reader = csv.reader(csv_file, delimiter=';')
            for i in tqdm (range (count), desc="Import Crews...", ncols=75):
                row = next(csv_reader)
                # break at end of file
                if row[0] == None:
                    break
                if line_count == 0:
                    line_count += 1
                else:
                    crew = copy.deepcopy(crewModel)
                    crew['name'] = row[0][9:]
                    crew['email'] = row[1]
                    crew['cities'].append(self.get_city(crew['name']))
                    result.append(crew)
                    line_count += 1
        return result
    
    def get_city(self, city_name):
        city = {
            'city': '',
            'country': '',
            'country_code': '',
            'place_id': ''
        }
        url_search = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        url_place = "https://maps.googleapis.com/maps/api/place/details/json?"
        r = requests.get(url_search + 'query=' + city_name  +
                                '&key=' + self.api_key)
        x = r.json()
        if len(x['results']) == 0:
            return
        y = x['results'][0]
        place_id = y['place_id']
        city['place_id'] = place_id
        r = requests.get(url_place + 'place_id=' + place_id +
                                '&key=' + self.api_key)
        result = r.json()
        address_components = result['result']["address_components"]
        for entry in address_components:
            if 'country' in entry['types']:
                city['country'] = entry['long_name']
                city['country_code'] = entry['short_name']
            elif 'locality' in entry['types']:
                city['city'] = entry['long_name']       
        return city
    
    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "migrate":
            self.migrate(argv[3])
