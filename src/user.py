from sqlite3 import Cursor
from pydantic import BaseModel
import pymysql, pymysql.cursors, os, copy, uuid
from dotenv import load_dotenv
import requests
from tqdm import tqdm
import pprint
import random, bcrypt

from .result import Result

from .utils import Utils , Modified

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
        'country': '',
        'country_code': '',
        'additionals': ''
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

class User(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    display_name: str
    drops_id: str
    modified: Modified

class UserHandler:

    def __init__(self) -> None:
        self.utils = Utils()
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.drops = self.utils.connect_drops()
        self.pool1 = self.utils.connect_pool1()


    def all(self, timestamp=None):

        where = ''
        if timestamp != None:
            where = ' and u.created > ' + timestamp

        sql = ('select u.public_id, p.email, s.first_name, s.last_name, u.created, u.updated from User as u ' 
            'left join Profile as p on u.id = p.user_id ' 
            'left join Supporter as s on s.profile_id = p.id ' 
            'where p.confirmed = 1' + where)
        with self.drops.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()
        result = []
        for x in sql_result:
            id = str(uuid.UUID(bytes=x['public_id']))
            modified=Modified(created=int(x['created']/1000), updated=int(x['updated']/1000))
            result.append(
                User(
                    id=id,
                    email=x['email'].lower(),
                    first_name=x['first_name'],
                    last_name=x['last_name'],
                    display_name="",
                    drops_id=id,
                    modified=modified
                )
            )
        return result
    
    def export(self, list):
        result = Result()
        for i in tqdm (range(len(list)), desc="Export Users to IDjango...", ncols=75):
            response = self.utils.idjango_post('/v1/pool/user/', list[i].dict())
            result.add(response)
        result.print()
    
    def getUsers(self, email=None):
        where = ''
        if email != None:
            where = 'where p.email = "' + email +'"'
        sql = ( 'select u.public_id, p.email, s.first_name, s.last_name, sc.active, sc.nvm_date, c.publicId as crew_publicId, u.created, u.updated, sc.pillar, s.birthday, s.mobile_phone, s.sex, '
                'sc.updated as crew_updated, sc.created as crew_created, a.country, a.street, a.zip, a.city, a.additional '
                'from User as u ' 
                'left join Profile as p on u.id = p.user_id ' 
                'left join Supporter as s on s.profile_id = p.id '
                'left join Address as a on a.supporter_id = s.id '
                'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                'left join Crew as c on sc.crew_id = c.id '  + where
                )
        with self.drops.cursor() as cursor:
            cursor.execute(sql)
            database_result = cursor.fetchall()
            result_dict = {}
        for i in tqdm (range (len(database_result)), desc="Convert User...", ncols=75):
            x = database_result[i]
            if x['email'] in result_dict.keys():
                result_dict[x['email']] = self.update_user(result_dict[x['email']], x)
            else:
                user = self.create_user(x)
                #profile
                user['profile'] = self.create_profile(x)  
                #address
                user['address'] = self.addressSearch(x)
                
                if x['crew_publicId'] != None:
                    user['crew'] = self.create_crew(x)
                result_dict[x['email']] = user

        result = []
        for x in result_dict:
            result.append(result_dict[x])
        return result
    
    def create_user(self, db_entry):
        user = copy.deepcopy(userModel)
        user['email'] = db_entry['email']
        user['drops_id'] = str(uuid.UUID(bytes=db_entry['public_id']))
        user['first_name'] = db_entry['first_name']
        user['last_name'] = db_entry['last_name']
        user['full_name'] = db_entry['first_name'] + ' ' + db_entry['last_name']
        user['modified']["created"] = int(db_entry['created'] /1000)
        user['modified']['updated'] = int(db_entry['updated'] /1000)
        if db_entry['active'] != None:
            user['active'] = db_entry['active']
        if db_entry['nvm_date'] !=None:
            user['nvm_date'] = int(db_entry['nvm_date'] / 1000)
        if db_entry['pillar'] != None:
            user['roles'].append(db_entry['pillar'])

        return user
    
    def update_user(self, user, db_entry):
        if db_entry['active'] != None:
            user['active'] = db_entry['active']
        if db_entry['nvm_date'] !=None:
            user['nvm_date'] = int(db_entry['nvm_date'] / 1000)
        if db_entry['pillar'] != None:
            user['roles'].append(db_entry['pillar'])
        return user


    # creates profile from db_entry
    def create_profile(self, db_entry):
        profile = {
            'birthdate': 0,
            'phone': db_entry['mobile_phone'],
            'gender': db_entry['sex'],
        }
        if db_entry['birthday'] != None:
            profile['birthdate'] = int(db_entry['birthday']/1000)
        return profile
    
    # creates crew form db_entry
    def create_crew(self, db_entry): 
        crew = { 
            'id': str(uuid.UUID(bytes=db_entry['crew_publicId'])),
            'modified': {
                'updated': int(db_entry['crew_created']/1000),
                'created': int(db_entry['crew_updated']/1000)
            },
        }
        return crew

    def addressSearch(self, db_entry): 
        address = {
            'street': '',
            'number': '',
            'zip': '',
            'city': '',
            'country': '',
            'country_code': '',
            'additionals': ''
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
        address[0]['additionals'] = db_entry['additional']
        #print(place_id)
        return address[0]

    def postUsers(self, u_list):
        count = {
            'success': 0,
            'failed': 0,
            'error': []
        }
        token = os.getenv('POOL3_KEY')
        if token == None:
            token = "secret"
        headers = {'Content-Type': 'application/json', "Authorization": "Bearer " + token}
        url = os.getenv('POOL3_ADMIN_URL')
        if url == None:
            url = "http://pool-api.localhost"

        for i in tqdm (range (len(u_list)), desc="Import User...", ncols=75):
            response = requests.post(url + '/migrations/user', headers=headers, json=u_list[i])
            if response.status_code != 201:
                count['failed'] = count['failed'] +1
                count['error'].append(response.text)
            else:
                count['success'] = count['success'] + 1
        return count

    def migrate(self):
        user = self.getUsers()
        #for x in user:
        #    if x['address'] != None:
        #        print(x)
        result = self.postUsers(user)
        print("Import User completed.")
        if len(result["error"]) != 0:
            print('Errors: ')
            for x in result['error']:
                print(x)
        print("Success: ", result['success'])
        print("Failed: ", result['failed'])
    
    def confirm(self, email):
        sql = "update Profile set confirmed = 1 where email = %s"
        with self.drops.cursor() as cursor:
            cursor.execute(sql, email)
        self.drops.commit()

    def get(self, email):
        sql = "select * from User as u left join Profile as p on p.user_id = u.id where email = %s"
        with self.drops.cursor() as cursor:
            cursor.execute(sql, email)
            database_result = cursor.fetchone()
            print(database_result)

    def change_password(self, email):
        password = ''
        for _ in range(20):
            random_integer = random.randint(33, 122)
            password += (chr(random_integer))
        password_bytes = bytes(password, 'utf8')
        password_hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(10))
        sql_update='update PasswordInfo as pi left join Profile as p on p.id = pi.profile_id set password = "' + password_hashed.decode() +'" where p.email = %s'
        with self.drops.cursor() as cursor:
            cursor.execute(sql_update, email)
            result = cursor.fetchone()
        sql = 'select * from Profile as p left join PasswordInfo as pi on pi.profile_id = p.id where email = %s'
        with self.drops.cursor() as cursor:
            cursor.execute(sql, email)
            result = cursor.fetchone()
            if not bcrypt.checkpw(password_bytes, result["password"].encode("utf-8")):
                print("Error: password not matching with database. Try again." )
        print("Password is: ", password)
    def delete(self, email):
        sql = "select p.id as p_id, u.id as u_id, s.id as s_id from User as u left join Profile as p on p.user_id = u.id left join Supporter as s on s.profile_id = p.id where email = %s"
        u_id = 0
        with self.drops.cursor() as cursor:
            cursor.execute(sql, email)
            database_result = cursor.fetchone()
            u_id = database_result["u_id"]
            p_id = database_result["p_id"]
            s_id = database_result["s_id"]
        login_del = "delete from LoginInfo where profile_id = " + str(p_id)
        password_del = "delete from PasswordInfo where profile_id = " + str(p_id)
        address_del = "delete from Address where supporter_id = " + str(s_id)
        supporter_del = "delete from Supporter where profile_id = " + str(p_id)
        supporter_crew_del = "delete from Supporter_Crew where supporter_id = " + str(s_id)
        profile_del = " delete from Profile where user_id = " + str(u_id)
        oauth_del = "delete o from OauthToken as o left join User as u on u.public_id = o.user_id where u.id = " + str(u_id)
        user_del = " delete from User where id = " + str(u_id)

        with self.drops.cursor() as cursor:
            cursor.execute(login_del)
            cursor.execute(password_del)
            cursor.execute(supporter_crew_del)
            cursor.execute(address_del)
            cursor.execute(supporter_del)
            cursor.execute(profile_del)
            cursor.execute(oauth_del)
            cursor.execute(user_del)
        self.drops.commit()
        
        del_p1_user = "select * from wp_users where user_email = %s"
        with self.pool1.cursor() as cursor:
            cursor.execute(del_p1_user, email)
            database_result = cursor.fetchone()
            u_id = database_result["ID"]
        user_del = "delete from wp_users where id = " + str(u_id)
        with self.pool1.cursor() as cursor:
            cursor.execute(user_del)
        self.pool1.commit()


    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "migrate":
            self.migrate()
        if argv[2] == "confirm":
            self.confirm(argv[3])
            self.get(argv[3])
        if argv[2] == "get":
            result = self.getUsers(argv[3])
            for i in result:
                pprint.pprint(i)
        if argv[2] == "delete":
            self.delete(argv[3])
        if argv[2] == 'all':
            result = self.all()
            print(result)
        if argv[2] == 'export':
            result = self.all(argv[3])
            self.export(result)
        if argv[2] == 'change_password':
            self.change_password(argv[3])


