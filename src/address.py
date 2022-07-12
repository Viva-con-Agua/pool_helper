
import os
from email import utils
from typing import List
import uuid
from pydantic import BaseModel
from tqdm import tqdm

from .result import Result
from .utils import Utils
import requests
from pydantic.dataclasses import dataclass

class Address(BaseModel):
    street: str
    number: str
    zip: str
    city: str
    country: str
    country_code: str
    additionals: str
    user_id: str


class AddressHandler:

    def __init__(self):
        self.utils = Utils()
        self.drops = self.utils.connect_drops()
        self.url_search = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        self.url_place = "https://maps.googleapis.com/maps/api/place/details/json?"    
        self.api_key = os.getenv('GOOGLE_API_KEY')

    def all(self, timestamp=None):

        where = ''
        if timestamp != None:
            where = ' where u.created > ' + timestamp

        sql = ('select * from Address as a '
        'left join Supporter as s on a.supporter_id = s.id '
        'left join Profile as p on s.profile_id = p.id '
        'left join User as u on u.id = p.user_id' + where)
        with self.drops.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()
        print("Select all addresses from database")
        result = []
        for i in tqdm (range(len(sql_result)), desc="Get True address from google...", ncols=75):
            a = self.addressSearch(sql_result[i])
            if a != None:
                result.append(a)
        return result

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


        # get method of requests module
        # return response object

        if db_entry['street'] == None or db_entry['zip'] == None or db_entry['street'] == '' or db_entry["zip"] == "":
            return None
        r = requests.get(self.url_search + 'query=' + db_entry['street'] + '%2C%20' + db_entry['zip'] +
                                '&key=' + self.api_key)
          
        # json method of response object convert
        #  json format data into python format data
        x = r.json()
        # now x contains list of nested dictionaries
        # we know dictionary contain key value pair
        # store the value of result key in variable y
        if len(x['results']) == 0:
            print("result")
            return
        y = x['results'][0]
        place_id = y['place_id']
        r = requests.get(self.url_place + 'place_id=' + place_id +
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
        result = Address(
            street=address[0]['street'],
            number=address[0]['number'],
            zip=address[0]['zip'],
            city=address[0]['city'],
            country=address[0]['country'],
            country_code=address[0]['country_code'],
            additionals=db_entry['additional'],
            user_id=str(uuid.UUID(bytes=bytes(db_entry["u.public_id"])))
        )
        return result

    def export(self, list):
        result = Result()
        for i in tqdm (range(len(list)), desc="Export Address to IDjango...", ncols=75):
            response = self.utils.idjango_post('/v1/pool/address/', list[i].dict())
            result.add(response)
        result.print()


    def process(self, argv):
        if len(argv) < 2:
            exit("missing parameter. Use -h for infos.")
        else:
            func = argv[2]
        if func == "all":
            result = self.all()
            for i in result:
                print(i)
        elif func == "export":
            result = self.all()
            self.export(result)

    
