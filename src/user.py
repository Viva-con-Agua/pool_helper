from sys import argv
import pymysql, pymysql.cursors, os, copy, uuid
from dotenv import load_dotenv
import requests
from tqdm import tqdm 

userModel = {
#    'id': '',
    'email': '',
    'first_name': '',
    'last_name': '',
    'full_name': '',
    'drops_id': '',
    'crew': { 
        'id':'',
        'modified': {
            'updated': 0,
            'created': 0
        },
    },
    'active': '',
    'nvm_date': 0,
    'modified': {
        'updated': 0,
        'created': 0
    },
    'address': {
        'street': '',
        'number': '',
        'zip': '',
        'city': '',
        'country': 'country',
        'country_code': '',
    },
    'profile': {
        'birthdate': 0,
        'phone': '',
        'gender': '',
    },
    'roles': []

#    'country': '',
#    'privacy_policy': '',
#    'confirmed': '',
}

class User:

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
    
    def getUsers(self):
        sql = ( 'select u.public_id, p.email, s.first_name, s.last_name, sc.active, sc.nvm_date, c.publicId, u.created, u.updated, sc.pillar, s.birthday, s.mobile_phone, s.sex, '
                'sc.updated as crew_updated, sc.created as crew_created, a.country, a.street, a.zip, a.city '
                'from User as u ' 
                'left join Profile as p on u.id = p.user_id ' 
                'left join Supporter as s on s.profile_id = p.id '
                'left join Address as a on a.supporter_id = s.id '
                'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                'left join Crew as c on sc.crew_id = c.id '
                'limit 200'
                )
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            database_result = cursor.fetchall()
            result_dict = {}
        for i in tqdm (range (len(database_result)), desc="Convert User...", ncols=75):
            x = database_result[i]
            if x['email'] in result_dict.keys():
                if x['active'] != None:
                    result_dict[x['email']]["active"] = x['active']
                if x['nvm_date'] !=None:
                    result_dict[x['email']]['nvm_date'] = x['nvm_date']
                if x['pillar'] != None:
                    result_dict[x['email']]['roles'].append(x['pillar'])
            else:
                user = copy.deepcopy(userModel)
                user['email'] = x['email']
                user['drops_id'] = str(uuid.UUID(bytes=x['public_id']))
                user['first_name'] = x['first_name']
                user['last_name'] = x['last_name']
                user['full_name'] = x['first_name'] + ' ' + x['last_name']
                #profile
                user['profile'] = self.create_profile(x)  
                user['address'] = self.addressSearch(x)
                if x['publicId'] != None:
                    user['crew']['id'] = str(uuid.UUID(bytes=x['publicId']))
                    user['crew']['modified']['created'] = x['crew_created'] 
                    user['crew']['modified']['updated'] = x['crew_updated']
               # user['crew_id'] = str(uuid.UUID(bytes=x['publicId']))
                if x['active'] != None:
                    user['active'] = x['active']
                if x['nvm_date'] !=None:
                    user['nvm_date'] = x['nvm_date']
                if x['pillar'] != None:
                    user['roles'].append(x['pillar'])
                result_dict[x['email']] = user

        result = []
        for x in result_dict:
            result.append(result_dict[x])
        return result
    


    def create_profile(self, db_entry):
        profile = {
            'birthdate': db_entry['birthday'],
            'phone': db_entry['mobile_phone'],
            'gender': db_entry['sex'],
        }
        return profile

    def clean_country(self, country):
        if country == None:
            return ''
        elif 'deuts' in country.lower() or 'german' in country.lower() or 'nieder' in country.lower():
            return 'Deutschland'
        elif 'öster' in country.lower() or 'aust' in country.lower():
            return 'Österreich'
        elif 'schweiz' in country.lower() or 'switz' in country.lower():
            return 'Schweiz'
        elif 'denmark' in country.lower() or 'dänemark' in country.lower():
            return 'Dänemark'
        elif 'spain' in country.lower():
            return 'Spanien'
        elif 'south' in country.lower():
            return 'Südafrika'
        else:
            return country

    def country_code(self, country): 
        if country == None:
            return ''
        elif country == 'Deutschland':
            return 'DE'
        elif country == 'Österreich':
            return 'AT'
        elif country == 'Schweiz':
            return 'CH'
        elif country == 'Dänemark':
            return 'DK'
        elif country == 'Spanien':
            return 'ES'
        elif country == 'Südafrika':
            return 'ZA'

    def addressSearch(self, db_entry): 
        address = {
            'street': '',
            'number': '',
            'zip': '',
            'city': '',
            'country': '',
            'country_code': '',
        },
        # enter your api key here
        #api_key = 'AIzaSyAX6zQOta_rs-AZYJWGPZ4YSTNMPeVQ8q0'


        # url variable store url
        url_search = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        url_place = "https://maps.googleapis.com/maps/api/place/details/json?"
        # The text string on which to search
          
        # get method of requests module
        # return response object
        if db_entry['street'] == None or db_entry['zip'] == None:
            return
        r = requests.get(url_search + 'query=' + db_entry['street'] + '%2C%20' + db_entry['zip'] +
                                '&key=' + self.api_key)
          
        # json method of response object convert
        #  json format data into python format data
        x = r.json()
        # now x contains list of nested dictionaries
        # we know dictionary contain key value pair
        # store the value of result key in variable y
        if len(x['results']) == 0:
            return
        y = x['results'][0]
        place_id = y['place_id']
        r = requests.get(url_place + 'place_id=' + place_id +
                                '&key=' + self.api_key)
        result = r.json()
        address_components = result['result']["address_components"]
        for entry in address_components:
            if 'street_number' in entry['types']:
                #print(entry['long_name'])
                address[0]['number'] = entry['long_name']
            elif 'route' in entry['types']:
                address[0]['street'] = entry['long_name']
            elif 'country' in entry['types']:
                address[0]['country'] = entry['long_name']
                address[0]['country_code'] = entry['short_name']
            elif 'postal_code' in entry['types']:
                address[0]['zip'] = entry['long_name']
            elif 'locality' in entry['types']:
                address[0]['city'] = entry['long_name']       
            #print(entry)
        #print(place_id)
        return address[0]

    def postUsers(self, u_list):
        headers = {'Content-Type': 'application/json'}
        url = os.getenv('POOL3_ADMIN_URL')
        if url == None:
            url = "http://localhost:1340"

        for i in tqdm (range (len(u_list)), desc="Import User...", ncols=75):
            response = requests.post(url + '/admin/users', headers=headers, json=u_list[i])
            if response.status_code != 201:
                print(response)
        print("Import User successfully completed.")

    def migrate(self):
        user = self.getUsers()
        #self.addressSearch('Meerweibchenstraße 3')
        for x in user:
            if x['address'] != None:
                print(x)
        #self.postUsers(user)
       


    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "migrate":
            self.migrate()
