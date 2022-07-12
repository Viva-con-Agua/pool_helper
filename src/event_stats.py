import os
import copy

import pymysql 
import pymysql.cursors

from dotenv.main import load_dotenv


class EventStats:

    def __init__(self) -> None:
        load_dotenv()
        password=os.getenv('POOL1_PASSWORD')
        if password == None:
            print("set pool1 pw")
            exit(1)
        port_string= os.getenv("POOL1_PORT")
        if port_string != None:
            port = int(port_string)
        else:
            port = 3306
        self.pool1 = pymysql.connect(
                host=os.getenv('POOL1_HOST'),
                port=port,
                user=os.getenv('POOL1_USER'),
                password=password,
                database="db175370026",
                cursorclass=pymysql.cursors.DictCursor
                )

    def get_event(self):
        user = {
                'email':'',
                'created': ''
                }
        sql = ('select * from wp_posts as p left join wp_vca_asm_applications as a on a.activity = p.id left join wp_users as u on u.id = a.supporter where post_type = "festival"')
        with self.pool1.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
        event = {}
        for x in result:
            u = copy.deepcopy(user)
            u['email'] = x["user_email"]
            u['created'] = str(x["user_registered"])
            if x["post_name"] in event.keys():
                event[x["post_name"]].append(u)
            else:
                event[x["post_name"]] = [u]
        for y in event.keys():
            print(y)
            for us in event[y]:
                print("\tEmail: ", us['email'], "Created: ", us['created'])
            print("\n")

    def get_postmeta_keys(self):
        sql = ('select * from wp_usermeta')
        with self.pool1.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
        keys = []
        for x in result:
            keys.append(x['meta_key'])
        l = list(set(keys))
        l.sort()
        for x in l:
             print(x)

    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "meta_key":
            self.get_postmeta_keys()
        if argv[2] == "get":
            self.get_event()


