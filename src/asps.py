from typing import List
from uuid import UUID
import pymysql, pymysql.cursors, os, getopt, sys, csv
from pymysql import connections
from dotenv import load_dotenv
import time
import datetime
from pydantic import BaseModel
from .utils import Utils


class ExportASP(BaseModel):
    uuid: str
    role: str

class ExportASPCrew(BaseModel):
    crew_id: str
    users: List[ExportASP]

class Asps:
    def __init__(self):
        self.utils = Utils()
        self.drops = self.utils.connect_drops()
    

    def parse_csv(self, file):
        result = {}
        with open(file) as csv_file:
            csv_reader= csv.reader(csv_file, delimiter=';')
            line_count = 0
            for row in csv_reader:
                if row[0] == None:
                    break
                if line_count == 0:
                    line_count += 1
                else:
                    try:
                        if row[0] not in result:
                            result[row[0]] = [{"email": row[2], "role": row[3] }]
                        else:
                            result[row[0]].append({"email": row[2], "role": row[3]})
                    except Exception as e:
                        print(e)
                    line_count += 1
        return result
 
    # crew, Name, email, pillar
    def set_list(self, file):
        with open(file) as csv_file:
            csv_reader= csv.reader(csv_file, delimiter=';')
            line_count = 0
            for row in csv_reader:
                if row[0] == None:
                    break
                if line_count == 0:
                    line_count += 1
                else:
                    try:
                        self.set(row[2], row[0], row[3])
                    except Exception as e:
                        print(e)
                    line_count += 1
            print(line_count)

    def all(self, crew):
        if crew != None:
            crew = 'and c.name = "' + crew + '"'
        else:
            crew = ""
        with self.drops.cursor() as cursor:
            sql = 'select p.email, s.full_name, c.name, sc.role, sc.pillar from Profile as p left join Supporter as s on p.id = s.profile_id left join Supporter_Crew as sc on sc.supporter_id = s.id left join Crew as c on c.id = sc.crew_id where sc.role = "VolunteerManager" ' + crew
            cursor.execute(sql)
            result = cursor.fetchall()
            print(result)


    def get(self, email=None, crew=None):
        if email != None and crew != None:
            where = 'where p.email = ' + '"' + email +'"' + ' and c.name = ' + '"'+crew+'"'
        elif email != None:
            where = 'where p.email = ' + '"' + email + '"'
        elif crew != None:
            where = 'where c.name = ' + '"'+crew+'"'
        else:
            print("error")
            exit(1)

        with self.drops.cursor() as cursor:
            sql = ('select p.email, s.full_name, c.name, sc.role, sc.pillar, sc.updated, sc.created, c.publicId '
                'from Profile as p '
                'left join Supporter as s on p.id = s.profile_id '
                'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                'left join Crew as c on c.id = sc.crew_id ' + where )
            cursor.execute(sql)
            result = cursor.fetchall()
            print(result)
    
    def clean_roles(self):
        sql_socialmedia = ('update Supporter_Crew set pillar = "socialmedia" where pillar = "social media"')
        sql_additonal = ('update Supporter_Crew set pillar = "additonals" where pillar = "zusätzliche"')
        sql_awareness = ('update Supporter_Crew set pillar = "awareness" where pillar = "Awareness"')
        with self.drops.cursor() as cursor:
            cursor.execute(sql_socialmedia)
            cursor.execute(sql_additonal)
            cursor.execute(sql_awareness)
        self.drops.commit()

    def get_crews(self, crew=None) -> List:
        where = ""
        if crew != None:
            where = 'where name = ' + '"'+ crew + '"'
        with self.drops.cursor() as cursor:
            sql = ('select name from Crew ' + where)
            cursor.execute(sql)
            result = cursor.fetchall()
        return result


    def set(self, email, crew, pillar):
        presentDate = datetime.datetime.now()
        unix_timestamp = datetime.datetime.timestamp(presentDate)*1000
        with self.drops.cursor() as cursor:
            sql = ('select s.id from Profile as p left join Supporter as s on s.profile_id = p.id '
                    'where LOWER(email) = %s')
            cursor.execute(sql, (email.lower(),))
            result = cursor.fetchone()
            if result != None:
                s_id = result["id"]
            else:
                raise Exception(email + " -- No Profile with given email ")
            sql = ('select c.id from Crew as c where c.name = %s')
            cursor.execute(sql, (crew,))
            result = cursor.fetchone()
            if result != None:
                c_id = result["id"]
            else:
                raise Exception("No Crew with given crew " + crew)

        with self.drops.cursor() as cursor:
            # Create a new record
            sql = ("insert into Supporter_Crew " 
                    "(`supporter_id`, `crew_id`, `role`, `pillar`, `updated`, `created`, `active`, `nvm_date` )"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            cursor.execute(sql, (s_id, c_id, "VolunteerManager", pillar.rstrip(), unix_timestamp, unix_timestamp, None, None,  ))

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        self.drops.commit()
    
    
    
    def delete_crew_csv(self, file):
        with open(file) as csv_file:
            csv_reader= csv.reader(csv_file, delimiter=';')
            line_count = 0
            crews = []
            for row in csv_reader:
                if row[0] == None:
                    break
                if line_count == 0:
                    line_count += 1
                else:
                    crews.append(row[0])
                    line_count += 1
            crews = list(set(crews))
            for crew in crews:
                self.delete_for_crew(crew)



    def delete_for_crew(self, crew):
        with self.drops.cursor() as cursor:
            sql = ('select p.email, s.full_name, c.name, sc.role, sc.pillar '
                    'from Profile as p '
                    'left join Supporter as s on p.id = s.profile_id '
                    'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                    'left join Crew as c on c.id = sc.crew_id '
                    'where sc.role = "VolunteerManager" and c.name = %s')
            cursor.execute(sql, (crew,))
            result = cursor.fetchall()
            email_list = []
            for e in result:
                email_list.append(e["email"])
            email_list = list(set(email_list))
            for email in email_list:
                self.delete(email)

    def create_export(self, crew):
        with self.drops.cursor() as cursor:
            sql = ('select u.public_id,  p.email, s.full_name, c.name, sc.role, sc.pillar, sc.updated, sc.created, c.publicId as crew_id '
                'from User as u '
                'left join Profile as p on u.id = p.user_id '
                'left join Supporter as s on p.id = s.profile_id '
                'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                'left join Crew as c on c.id = sc.crew_id '
                'where c.name = %s && sc.role = "VolunteerManager"' )
            cursor.execute(sql, crew)
            result = cursor.fetchall()
        if result:
            exportCrew = ExportASPCrew(crew_id=str(UUID(bytes=result[0]["crew_id"])), users=[])
            for i in result:
                user = ExportASP(uuid=str(UUID(bytes=i["public_id"])), role=i["pillar"])
                exportCrew.users.append(user)
            response = self.utils.idjango_post('/v1/pool/asps/', exportCrew.dict())
            print(response.text)
        else:
            print(crew + " not found!")
        
       

    def process(self, argv):
        func = argv[2]
        if func == "csv":
            parse = self.parse_csv(argv[3])
            for entry in parse.keys():
                self.delete_for_crew(entry)
                for e in parse[entry]:
                    self.set(e["email"], entry, e["role"])
            for entry in parse.keys():
                self.create_export(entry) 
        elif func == "export":
            options = "hc:"
            long = "help", "crew="
            crew = None
            try:
                a, _ = getopt.getopt(argv[3:], options, long)
                for ca, cv in a:
                    if cv in ("-h", "--help"):
                        print(help)
                    elif ca in ("-c", "--crew"):
                        crew = cv
            except getopt.error as err:
                print(str(err))
            result = self.get_crews(crew)
            for entry in result:
                self.create_export(entry["name"])
        

        elif func == "all":
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
            self.all(crew)
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
            self.get(email, crew)
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
                self.delete_crew_csv(csv)
                self.set_list(csv)
                exit(0)
            self.set(email, crew, pillar)

        elif func == "delete":
            options = "he:c:l:"
            long = ["help", "email=", "crew=", "list="]
            crew  = None 
            email = None
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
            except getopt.error as err:
                # output error, and return with an error code
                print (str(err))
            if csv != None:
                self.delete_crew_csv(csv)
                exit(0)
            if email != None and crew != None:
                print("-e takes no effect in with -c")
            elif crew != None: 
                self.delete_for_crew(crew)
                exit(0) 
            elif email != None:
                self.delete(email)
                exit(0)
            else:
                print("error")
                exit(1)
        elif func == "clean":
            self.clean_roles()








#    def set(self, email, crew, pillar):
#        with self.connection.cursor() as cursor:
#            sql = ('select s.id from Profile as p left join Supporter as s on s.profile_id = p.id '
#                    'where LOWER(email) = %s')
#            cursor.execute(sql, (email.lower(),))
#            result = cursor.fetchone()
#            if result == None:
#                raise Exception(email + " -- No Profile with given email ")
#        print("update " + email)
#        if email != None:
#            where = 'where LOWER(p.email) = ' + '"' + email + '" ' +'and c.name = "' + crew + '"'
#        else:
#            print("error")
#            exit(1)
#        with self.connection.cursor() as cursor:
#            sql = ('update Supporter_Crew as sc '
#                    'left join Supporter as s on sc.supporter_id = s.id '
#                    'left join Profile as p on s.profile_id = p.id '
#                    'left join Crew as c on c.id = sc.crew_id ' 
#                    'set sc.pillar = %s, sc.role = "VolunteerManager" '
#                    + where
#                )
#            cursor.execute(sql, pillar.lstrip())
#        self.connection.commit()

    def delete(self, email):
        print("update " + email)
        if email != None:
            where = 'where LOWER(p.email) = ' + '"' + email + '" and sc.role = "VolunteerManager"'
        else:
            print("error")
            exit(1)
        with self.drops.cursor() as cursor:
            sql = ('update Supporter_Crew as sc '
                    'left join Supporter as s on sc.supporter_id = s.id '
                    'left join Profile as p on s.profile_id = p.id '
                    'left join Crew as c on c.id = sc.crew_id ' 
                    'set sc.pillar = NULL, sc.role = NULL '
                    + where
                )
            cursor.execute(sql)
        self.drops.commit()
